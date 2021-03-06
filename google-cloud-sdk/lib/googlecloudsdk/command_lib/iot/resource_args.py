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
"""Shared resource flags for Cloud IoT commands."""

from googlecloudsdk.calliope.concepts import concept_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.core import properties


def DeviceAnchorAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='id',
      help_text='ID of the device.')


def RegistryAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='registry',
      help_text='The device registry for the {resource}.')


def RegistryAnchorAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='id',
      help_text='ID of the device registry.')


def RegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text='The Cloud region for the {resource}.')


def RegionAnchorAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text='The Cloud region.')


def ProjectAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='project',
      help_text='The Cloud project for the {resource}.',
      prop=properties.VALUES.core.project)


def GetDeviceResourceSpec():
  return concepts.ResourceSpec(
      'cloudiot.projects.locations.registries.devices',
      resource_name='device',
      devicesId=DeviceAnchorAttributeConfig(),
      registriesId=RegistryAttributeConfig(),
      locationsId=RegionAttributeConfig(),
      projectsId=ProjectAttributeConfig())


def GetRegistryResourceSpec():
  return concepts.ResourceSpec(
      'cloudiot.projects.locations.registries',
      resource_name='registry',
      registriesId=RegistryAnchorAttributeConfig(),
      locationsId=RegionAttributeConfig(),
      projectsId=ProjectAttributeConfig())


def GetRegionResourceSpec():
  return concepts.ResourceSpec(
      'cloudiot.projects.locations',
      resource_name='region',
      locationsId=RegionAnchorAttributeConfig(),
      projectsId=ProjectAttributeConfig())


def AddDeviceResourceArg(parser, verb, positional=True):
  """Add a resource argument for a cloud IOT device.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the device ID is a positional rather
      than a flag.
  """
  if positional:
    name = 'device'
  else:
    name = '--device'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetDeviceResourceSpec(),
      'The device {}.'.format(verb),
      required=True).AddToParser(parser)


def AddRegistryResourceArg(parser, verb, positional=True):
  """Add a resource argument for a cloud IOT device registry.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the device ID is a positional rather
      than a flag.
  """
  if positional:
    name = 'registry'
  else:
    name = '--registry'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetRegistryResourceSpec(),
      'The device registry {}.'.format(verb),
      required=True).AddToParser(parser)


def AddRegionResourceArg(parser, verb):
  """Add a resource argument for a cloud IOT region.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--region',
      GetRegionResourceSpec(),
      'The Cloud region {}.'.format(verb),
      required=True).AddToParser(parser)
