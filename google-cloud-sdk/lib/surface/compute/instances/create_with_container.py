# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Command for creating VM instances running Docker images."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import zone_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.util import labels_util
from googlecloudsdk.core import log


def _Args(parser, release_track):
  """Add flags shared by all release tracks."""
  parser.display_info.AddFormat(instances_flags.DEFAULT_LIST_FORMAT)
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser, True)
  instances_flags.AddCreateDiskArgs(parser)
  instances_flags.AddLocalSsdArgsWithSize(parser)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(parser, instances=True)
  instances_flags.AddMachineTypeArgs(parser)
  deprecate_maintenance_policy = release_track in [base.ReleaseTrack.ALPHA]
  instances_flags.AddMaintenancePolicyArgs(parser, deprecate_maintenance_policy)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(parser, False)
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddPrivateNetworkIpArgs(parser)
  instances_flags.AddKonletArgs(parser)
  instances_flags.AddPublicDnsArgs(parser, instance=True)
  instances_flags.AddPublicPtrArgs(parser, instance=True)
  instances_flags.AddImageArgs(parser)
  instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.ALPHA)
  labels_util.AddCreateLabelsFlags(parser)

  parser.add_argument(
      '--description',
      help='Specifies a textual description of the instances.')

  instances_flags.INSTANCES_ARG.AddArgument(parser, operation_type='create')

  CreateWithContainer.SOURCE_INSTANCE_TEMPLATE = (
      instances_flags.MakeSourceInstanceTemplateArg())
  CreateWithContainer.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateWithContainer(base.CreateCommand):
  """Command for creating VM instances running container images."""

  @staticmethod
  def Args(parser):
    """Register parser args."""
    _Args(parser, release_track=base.ReleaseTrack.BETA)

  def GetSourceInstanceTemplate(self, args, resources):
    if not args.IsSpecified('source_instance_template'):
      return None
    ref = self.SOURCE_INSTANCE_TEMPLATE.ResolveAsResource(args, resources)
    return ref.SelfLink()

  def _GetSkipDefaults(self, source_instance_template):
    # gcloud creates default values for some fields in Instance resource
    # when no value was specified on command line.
    # When --source-instance-template was specified, defaults are taken from
    # Instance Template and gcloud flags are used to override them - by default
    # fields should not be initialized.
    return source_instance_template is not None

  def _ValidateBetaArgs(self, args):
    instances_flags.ValidateKonletArgs(args)
    instances_flags.ValidateDiskCommonFlags(args)
    instances_flags.ValidateLocalSsdFlags(args)
    instances_flags.ValidateServiceAccountAndScopeArgs(args)
    if instance_utils.UseExistingBootDisk(args.disk or []):
      raise exceptions.InvalidArgumentException(
          '--disk',
          'Boot disk specified for containerized VM.')

  def _GetScheduling(self, args, client, skip_defaults):
    if (skip_defaults and not args.IsSpecified('maintenance_policy') and
        not args.IsSpecified('preemptible') and
        not args.IsSpecified('restart_on_failure')):
      return None
    else:
      return instance_utils.CreateSchedulingMessage(
          messages=client.messages,
          maintenance_policy=args.maintenance_policy,
          preemptible=args.preemptible,
          restart_on_failure=args.restart_on_failure)

  def _IsAnySpecified(self, args, *dests):
    return any([args.IsSpecified(dest) for dest in dests])

  def _GetServiceAccounts(self, args, client, skip_defaults):
    if args.no_service_account:
      service_account = None
    else:
      service_account = args.service_account
    if (skip_defaults and not self._IsAnySpecified(
        args, 'scopes', 'no_scopes', 'service_account', 'no_service_account')):
      return []
    else:
      return instance_utils.CreateServiceAccountMessages(
          messages=client.messages,
          scopes=[] if args.no_scopes else args.scopes,
          service_account=service_account)

  def _GetValidatedMetadata(self, args, client):
    user_metadata = metadata_utils.ConstructMetadataMessage(
        client.messages,
        metadata=args.metadata,
        metadata_from_file=args.metadata_from_file)
    containers_utils.ValidateUserMetadata(user_metadata)
    return user_metadata

  def _GetBootDiskSizeGb(self, args):
    boot_disk_size_gb = utils.BytesToGb(args.boot_disk_size)
    utils.WarnIfDiskSizeIsTooSmall(boot_disk_size_gb, args.boot_disk_type)
    return boot_disk_size_gb

  def _GetInstanceRefs(self, args, client, holder):
    instance_refs = instances_flags.INSTANCES_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetDefaultScopeLister(client))
    # Check if the zone is deprecated or has maintenance coming.
    zone_resource_fetcher = zone_utils.ZoneResourceFetcher(client)
    zone_resource_fetcher.WarnForZonalCreation(instance_refs)
    return instance_refs

  def _GetNetworkInterfaces(
      self, args, client, holder, instance_refs, skip_defaults):
    if (skip_defaults and not args.IsSpecified('network') and not
        self._IsAnySpecified(
            args, 'subnet', 'private_network_ip', 'no_address', 'address',
            'no_public_ptr', 'public_ptr', 'no_public_ptr_domain',
            'public_ptr_domain')):
      return []
    else:
      return [instance_utils.CreateNetworkInterfaceMessage(
          resources=holder.resources,
          compute_client=client,
          network=args.network,
          subnet=args.subnet,
          private_network_ip=args.private_network_ip,
          no_address=args.no_address,
          address=args.address,
          instance_refs=instance_refs,
          no_public_ptr=args.no_public_ptr,
          public_ptr=args.public_ptr,
          no_public_ptr_domain=args.no_public_ptr_domain,
          public_ptr_domain=args.public_ptr_domain,
      )]

  def _GetMachineTypeUris(
      self, args, client, holder, instance_refs, skip_defaults):
    if (skip_defaults and not args.IsSpecified('machine_type') and
        not args.IsSpecified('custom_cpu') and
        not args.IsSpecified('custom_memory')):
      return [None for _ in instance_refs]
    else:
      return instance_utils.CreateMachineTypeUris(
          resources=holder.resources,
          compute_client=client,
          machine_type=args.machine_type,
          custom_cpu=args.custom_cpu,
          custom_memory=args.custom_memory,
          ext=getattr(args, 'custom_extensions', None),
          instance_refs=instance_refs)

  def GetImageUri(self, args, client, holder, instance_refs):
    if (args.IsSpecified('image') or args.IsSpecified('image_family') or
        args.IsSpecified('image_project')):
      image_expander = image_utils.ImageExpander(client, holder.resources)
      image_uri, _ = image_expander.ExpandImageFlag(
          user_project=instance_refs[0].project,
          image=args.image,
          image_family=args.image_family,
          image_project=args.image_project)
      if holder.resources.Parse(image_uri).project != 'cos-cloud':
        log.warn('This container deployment mechanism requires a '
                 'Container-Optimized OS image in order to work. Select an '
                 'image from a cos-cloud project (cost-stable, cos-beta, '
                 'cos-dev image families).')
    else:
      image_uri = containers_utils.ExpandKonletCosImageFlag(client)
    return image_uri

  def _GetLabels(self, args, client):
    args_labels = getattr(args, 'labels', None)
    labels = None
    if args_labels:
      labels = client.messages.Instance.LabelsValue(
          additionalProperties=[
              client.messages.Instance.LabelsValue.AdditionalProperty(
                  key=key, value=value)
              for key, value in sorted(args.labels.iteritems())])
    return labels

  def _GetCanIpForward(self, args, skip_defaults):
    if skip_defaults and not args.IsSpecified('can_ip_forward'):
      return None
    else:
      return args.can_ip_forward

  def Run(self, args):
    self._ValidateBetaArgs(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    source_instance_template = self.GetSourceInstanceTemplate(
        args, holder.resources)
    skip_defaults = self._GetSkipDefaults(source_instance_template)
    scheduling = self._GetScheduling(args, client, skip_defaults)
    service_accounts = self._GetServiceAccounts(args, client, skip_defaults)
    user_metadata = self._GetValidatedMetadata(args, client)
    boot_disk_size_gb = self._GetBootDiskSizeGb(args)
    instance_refs = self._GetInstanceRefs(args, client, holder)
    network_interfaces = self._GetNetworkInterfaces(
        args, client, holder, instance_refs, skip_defaults)
    machine_type_uris = self._GetMachineTypeUris(
        args, client, holder, instance_refs, skip_defaults)
    image_uri = self.GetImageUri(args, client, holder, instance_refs)
    labels = self._GetLabels(args, client)
    can_ip_forward = self._GetCanIpForward(args, skip_defaults)
    tags = containers_utils.CreateTagsMessage(client.messages, args.tags)

    requests = []
    for instance_ref, machine_type_uri in zip(instance_refs, machine_type_uris):
      metadata = containers_utils.CreateKonletMetadataMessage(
          client.messages, args, instance_ref.Name(), user_metadata)
      disks = self._CreateDiskMessages(
          holder, args, boot_disk_size_gb, image_uri, instance_ref,
          skip_defaults)
      request = client.messages.ComputeInstancesInsertRequest(
          instance=client.messages.Instance(
              canIpForward=can_ip_forward,
              disks=disks,
              description=args.description,
              labels=labels,
              machineType=machine_type_uri,
              metadata=metadata,
              minCpuPlatform=args.min_cpu_platform,
              name=instance_ref.Name(),
              networkInterfaces=network_interfaces,
              serviceAccounts=service_accounts,
              scheduling=scheduling,
              tags=tags),
          sourceInstanceTemplate=source_instance_template,
          project=instance_ref.project,
          zone=instance_ref.zone)

      requests.append((client.apitools_client.instances,
                       'Insert', request))

    return client.MakeRequests(requests)

  def _CreateDiskMessages(self, holder, args, boot_disk_size_gb, image_uri,
                          instance_ref, skip_defaults):
    """Creates API messages with disks attached to VM instance."""
    if (skip_defaults and not args.IsSpecified('disk') and not
        self._IsAnySpecified(
            args, 'create_disk', 'local_ssd', 'boot_disk_type',
            'boot_disk_device_name', 'boot_disk_auto_delete')):
      return []
    else:
      persistent_disks, _ = (
          instance_utils.CreatePersistentAttachedDiskMessages(
              holder.resources, holder.client, None, args.disk or [],
              instance_ref))
      persistent_create_disks = (
          instance_utils.CreatePersistentCreateDiskMessages(
              holder.client, holder.resources, None,
              getattr(args, 'create_disk', []), instance_ref))
      local_ssds = []
      for x in args.local_ssd or []:
        local_ssd = instance_utils.CreateLocalSsdMessage(
            holder.resources,
            holder.client.messages,
            x.get('device-name'),
            x.get('interface'),
            x.get('size'),
            instance_ref.zone,
            instance_ref.project)
        local_ssds.append(local_ssd)
      boot_disk = instance_utils.CreateDefaultBootAttachedDiskMessage(
          holder.client, holder.resources,
          disk_type=args.boot_disk_type,
          disk_device_name=args.boot_disk_device_name,
          disk_auto_delete=args.boot_disk_auto_delete,
          disk_size_gb=boot_disk_size_gb,
          require_csek_key_create=None,
          image_uri=image_uri,
          instance_ref=instance_ref,
          csek_keys=None)
      return (
          [boot_disk] + persistent_disks + persistent_create_disks + local_ssds)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateWithContainerAlpha(CreateWithContainer):
  """Alpha version of compute instances create-with-container command."""

  @staticmethod
  def Args(parser):
    _Args(parser, release_track=base.ReleaseTrack.ALPHA)

    instances_flags.AddNetworkTierArgs(parser, instance=True)

  def _GetNetworkInterfaces(
      self, args, client, holder, instance_refs, skip_defaults):
    if (skip_defaults and not args.IsSpecified('network') and not
        self._IsAnySpecified(
            args, 'subnet', 'private_network_ip', 'no_address', 'address',
            'network_tier', 'no_public_dns', 'public_dns', 'no_public_ptr',
            'public_ptr', 'no_public_ptr_domain', 'public_ptr_domain')):
      return []
    else:
      return [instance_utils.CreateNetworkInterfaceMessage(
          resources=holder.resources,
          compute_client=client,
          network=args.network,
          subnet=args.subnet,
          private_network_ip=args.private_network_ip,
          no_address=args.no_address,
          address=args.address,
          instance_refs=instance_refs,
          network_tier=getattr(args, 'network_tier', None),
          no_public_dns=getattr(args, 'no_public_dns', None),
          public_dns=getattr(args, 'public_dns', None),
          no_public_ptr=getattr(args, 'no_public_ptr', None),
          public_ptr=getattr(args, 'public_ptr', None),
          no_public_ptr_domain=getattr(args, 'no_public_ptr_domain', None),
          public_ptr_domain=getattr(args, 'public_ptr_domain', None))]

  def Run(self, args):
    self._ValidateBetaArgs(args)
    instances_flags.ValidateNetworkTierArgs(args)
    instances_flags.ValidatePublicDnsFlags(args)
    instances_flags.ValidatePublicPtrFlags(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    source_instance_template = self.GetSourceInstanceTemplate(
        args, holder.resources)
    skip_defaults = self._GetSkipDefaults(source_instance_template)
    scheduling = self._GetScheduling(args, client, skip_defaults)
    service_accounts = self._GetServiceAccounts(args, client, skip_defaults)
    user_metadata = self._GetValidatedMetadata(args, client)
    boot_disk_size_gb = self._GetBootDiskSizeGb(args)
    instance_refs = self._GetInstanceRefs(args, client, holder)
    network_interfaces = self._GetNetworkInterfaces(
        args, client, holder, instance_refs, skip_defaults)
    machine_type_uris = self._GetMachineTypeUris(
        args, client, holder, instance_refs, skip_defaults)
    image_uri = self.GetImageUri(args, client, holder, instance_refs)
    labels = self._GetLabels(args, client)
    can_ip_forward = self._GetCanIpForward(args, skip_defaults)
    tags = containers_utils.CreateTagsMessage(client.messages, args.tags)

    requests = []
    for instance_ref, machine_type_uri in zip(instance_refs, machine_type_uris):
      metadata = containers_utils.CreateKonletMetadataMessage(
          client.messages, args, instance_ref.Name(), user_metadata)
      disks = self._CreateDiskMessages(
          holder, args, boot_disk_size_gb, image_uri, instance_ref,
          skip_defaults)
      request = client.messages.ComputeInstancesInsertRequest(
          instance=client.messages.Instance(
              canIpForward=can_ip_forward,
              disks=disks,
              description=args.description,
              labels=labels,
              machineType=machine_type_uri,
              metadata=metadata,
              minCpuPlatform=args.min_cpu_platform,
              name=instance_ref.Name(),
              networkInterfaces=network_interfaces,
              serviceAccounts=service_accounts,
              scheduling=scheduling,
              tags=tags),
          sourceInstanceTemplate=source_instance_template,
          project=instance_ref.project,
          zone=instance_ref.zone)

      requests.append((client.apitools_client.instances,
                       'Insert', request))
    return client.MakeRequests(requests)


CreateWithContainer.detailed_help = {
    'brief':
        """\
    Creates Google Compute engine virtual machine instances running
    container images.
    """,
    'DESCRIPTION':
        """\
        *{command}* creates Google Compute Engine virtual
        machines that runs a Docker image. For example:

          $ {command} instance-1 --zone us-central1-a \
            --container-image=gcr.io/google-containers/busybox

        creates an instance called instance-1, in the us-central1-a zone,
        running the 'busybox' image.

        For more examples, refer to the *EXAMPLES* section below.
        """,
    'EXAMPLES':
        """\
        To run the gcr.io/google-containers/busybox image on an instance named
        'instance-1' that executes 'echo "Hello world"' as a run command, run:

          $ {command} instance-1 \
            --container-image=gcr.io/google-containers/busybox \
            --container-command='echo "Hello world"'

        To run the gcr.io/google-containers/busybox image in privileged mode,
        run:

          $ {command} instance-1 \
            --container-image=gcr.io/google-containers/busybox
            --container-privileged
        """
}
