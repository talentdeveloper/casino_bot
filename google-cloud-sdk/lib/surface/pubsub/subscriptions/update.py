# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Cloud Pub/Sub subscriptions update command."""
from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.command_lib.util import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """This feature is part of an invite-only release of the Cloud Pub/Sub API.

  Updates an existing Cloud Pub/Sub subscription.
  This feature is part of an invitation-only release of the underlying
  Cloud Pub/Sub API. The command will generate errors unless you have access to
  this API. This restriction should be relaxed in the near future. Please
  contact cloud-pubsub@google.com with any questions in the meantime.
  """

  @classmethod
  def Args(cls, parser):
    flags.AddSubscriptionResourceArg(parser, 'to update.')
    flags.AddSubscriptionSettingsFlags(parser, cls.ReleaseTrack(),
                                       is_update=True)

    labels_util.AddUpdateLabelsFlags(parser)

  @exceptions.CatchHTTPErrorRaiseHTTPException()
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A serialized object (dict) describing the results of the operation.
      This description fits the Resource described in the ResourceRegistry under
      'pubsub.projects.subscriptions'.

    Raises:
      An HttpException if there was a problem calling the
      API subscriptions.Patch command.
    """
    client = subscriptions.SubscriptionsClient()
    subscription_ref = util.ParseSubscription(args.subscription)

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      original_subscription = client.Get(subscription_ref)
      labels = labels_diff.Apply(
          client.messages.Subscription.LabelsValue,
          original_subscription.labels)
    else:
      labels = None
    result = client.Patch(
        subscription_ref,
        ack_deadline=args.ack_deadline,
        push_config=util.ParsePushConfig(args.push_endpoint),
        retain_acked_messages=args.retain_acked_messages,
        labels=labels,
        message_retention_duration=args.message_retention_duration)

    result = util.SubscriptionDisplayDict(result)
    log.UpdatedResource(subscription_ref.RelativeName(), kind='subscription')
    return result
