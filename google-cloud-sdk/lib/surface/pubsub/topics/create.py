# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Cloud Pub/Sub topics create command."""
from apitools.base.py import exceptions as api_ex

from googlecloudsdk.api_lib.pubsub import topics
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.command_lib.util import labels_util
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  """Creates one or more Cloud Pub/Sub topics.

  Creates one or more Cloud Pub/Sub topics.

  ## EXAMPLES

  To create a Cloud Pub/Sub topic, run:

    $ {command} mytopic
  """

  @staticmethod
  def Args(parser):
    flags.AddTopicResourceArg(parser, 'to create.', plural=True)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      A serialized object (dict) describing the results of the operation.
      This description fits the Resource described in the ResourceRegistry under
      'pubsub.projects.topics'.

    Raises:
      util.RequestFailedError: if any of the requests to the API failed.
    """
    client = topics.TopicsClient()

    labels = labels_util.Diff.FromCreateArgs(args).Apply(
        client.messages.Topic.LabelsValue)

    failed = []
    for topic_name in args.topic:
      topic_ref = util.ParseTopic(topic_name)

      try:
        result = client.Create(topic_ref, labels=labels)
      except api_ex.HttpError as error:
        exc = exceptions.HttpException(error)
        log.CreatedResource(topic_ref.RelativeName(), kind='topic',
                            failed=exc.payload.status_message)
        failed.append(topic_name)
        continue

      result = util.TopicDisplayDict(result)
      log.CreatedResource(topic_ref.RelativeName(), kind='topic')
      yield result

    if failed:
      raise util.RequestsFailedError(failed, 'create')
