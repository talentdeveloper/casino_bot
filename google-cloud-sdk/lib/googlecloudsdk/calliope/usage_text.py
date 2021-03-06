# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Generate usage text for displaying to the user."""

import argparse
import copy
import difflib
import re
import StringIO
import sys
import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments

LINE_WIDTH = 80
HELP_INDENT = 25


class HelpInfo(object):
  """A class to hold some the information we need to generate help text."""

  def __init__(self, help_text, is_hidden, release_track):
    """Create a HelpInfo object.

    Args:
      help_text: str, The text of the help message.
      is_hidden: bool, True if this command or group has been marked as hidden.
      release_track: calliope.base.ReleaseTrack, The maturity level of this
        command.
    """
    self.help_text = help_text or ''
    self.is_hidden = is_hidden
    self.release_track = release_track


class TextChoiceSuggester(object):
  """Utility to suggest mistyped commands.

  """
  _SYNONYM_SETS = [
      set(['create', 'add']),
      set(['delete', 'remove']),
      set(['describe', 'get']),
      set(['patch', 'update']),
  ]

  def __init__(self, choices=None):
    # A mapping of 'thing typed' to the suggestion that should be offered.
    # Often, these will be the same, but this allows for offering more currated
    # suggestions for more commonly misused things.
    self._choices = {}
    if choices:
      self.AddChoices(choices)

  def AddChoices(self, choices):
    """Add a set of valid things that can be suggested.

    Args:
      choices: [str], The valid choices.
    """
    for choice in choices:
      if choice not in self._choices:
        # Keep the first choice mapping that was added so later aliases don't
        # clobber real choices.
        self._choices[choice] = choice

  def AddAliases(self, aliases, suggestion):
    """Add an alias that is not actually a valid choice, but will suggest one.

    This should be called after AddChoices() so that aliases will not clobber
    any actual choices.

    Args:
      aliases: [str], The aliases for the valid choice.  This is something
        someone will commonly type when they actually mean something else.
      suggestion: str, The valid choice to suggest.
    """
    for alias in aliases:
      if alias not in self._choices:
        self._choices[alias] = suggestion

  def AddSynonyms(self):
    """Activate the set of synonyms for this suggester."""
    for s_set in TextChoiceSuggester._SYNONYM_SETS:
      valid_choices = set(self._choices.keys()) & s_set
      for choice in valid_choices:
        # Add all synonyms in the set as aliases for each real choice that is
        # valid.  This will never clobber the original choice that is there.
        # If none of the synonyms are valid choices, this will not add any
        # aliases for this synonym set.
        self.AddAliases(s_set, choice)

  def GetSuggestion(self, arg):
    """Find the item that is closest to what was attempted.

    Args:
      arg: str, The argument provided.

    Returns:
      str, The closest match.
    """
    if not self._choices:
      return None

    match = difflib.get_close_matches(arg.lower(),
                                      [unicode(c) for c in self._choices],
                                      1)
    if match:
      choice = [c for c in self._choices if unicode(c) == match[0]][0]
      return self._choices[choice]
    return self._choices[match[0]] if match else None


def _ApplyMarkdownItalic(msg):
  return re.sub(r'(\b[a-zA-Z][-a-zA-Z_0-9]*)',
                base.MARKDOWN_ITALIC + r'\1' + base.MARKDOWN_ITALIC, msg)


def GetPositionalUsage(arg, markdown=False):
  """Create the usage help string for a positional arg.

  Args:
    arg: parser_arguments.Argument, The argument object to be displayed.
    markdown: bool, If true add markdowns.

  Returns:
    str, The string representation for printing.
  """
  var = arg.metavar or arg.dest.upper()
  if markdown:
    var = _ApplyMarkdownItalic(var)
  if arg.nargs == '+':
    return u'{var} [{var} ...]'.format(var=var)
  elif arg.nargs == '*':
    return u'[{var} ...]'.format(var=var)
  elif arg.nargs == argparse.REMAINDER:
    return u'[-- {var} ...]'.format(var=var)
  elif arg.nargs == '?':
    return u'[{var}]'.format(var=var)
  else:
    return var


def _GetFlagMetavar(flag, metavar=None, name=None, markdown=False):
  """Returns a usage-separator + metavar for flag."""
  if metavar is None:
    metavar = flag.metavar or flag.dest.upper()
  separator = '=' if name and name.startswith('--') else ' '
  if isinstance(flag.type, arg_parsers.ArgList):
    metavar = flag.type.GetUsageMsg(bool(flag.metavar), metavar)
  if metavar == ' ':
    return ''
  if markdown:
    metavar = _ApplyMarkdownItalic(metavar)
  if separator == '=':
    metavar = separator + metavar
    separator = ''
  if flag.nargs in ('?', '*'):
    metavar = '[' + metavar + ']'
    separator = ''
  return separator + metavar


def _QuoteValue(value):
  """Returns value quoted, with preference for "..."."""
  quoted = repr(value)
  if quoted.startswith('u'):
    quoted = quoted[1:]
  if quoted.startswith("'") and '"' not in value:
    quoted = '"' + quoted[1:-1] + '"'
  return quoted


def GetFlagUsage(arg, brief=False, markdown=False, inverted=False, value=True):
  """Returns the usage string for a flag arg.

  Args:
    arg: parser_arguments.Argument, The argument object to be displayed.
    brief: bool, If true, only display one version of a flag that has
        multiple versions, and do not display the default value.
    markdown: bool, If true add markdowns.
    inverted: bool, If true display the --no-* inverted name.
    value: bool, If true display flag name=value for non-Boolean flags.

  Returns:
    str, The string representation for printing.
  """
  if inverted:
    names = [x.replace('--', '--no-', 1) for x in sorted(arg.option_strings)]
  else:
    names = sorted(arg.option_strings)
  metavar = arg.metavar or arg.dest.upper()
  if not value or brief:
    try:
      long_string = names[0]
    except IndexError:
      long_string = ''
    if not value or arg.nargs == 0:
      return long_string
    flag_metavar = _GetFlagMetavar(arg, metavar, name=long_string)
    return u'{flag}{metavar}'.format(
        flag=long_string,
        metavar=flag_metavar)
  if arg.nargs == 0:
    if markdown:
      usage = ', '.join([base.MARKDOWN_BOLD + x + base.MARKDOWN_BOLD
                         for x in names])
    else:
      usage = ', '.join(names)
  else:
    usage_list = []
    for name in names:
      flag_metavar = _GetFlagMetavar(arg, metavar, name=name, markdown=markdown)
      usage_list.append(
          u'{bb}{flag}{be}{flag_metavar}'.format(
              bb=base.MARKDOWN_BOLD if markdown else '',
              flag=name,
              be=base.MARKDOWN_BOLD if markdown else '',
              flag_metavar=flag_metavar))
    usage = ', '.join(usage_list)
    if arg.default and not getattr(arg, 'is_required',
                                   getattr(arg, 'required', False)):
      if isinstance(arg.default, list):
        default = ','.join(arg.default)
      elif isinstance(arg.default, dict):
        default = ','.join([u'{0}={1}'.format(k, v)
                            for k, v in sorted(arg.default.iteritems())])
      else:
        default = arg.default
      usage += u'; default={0}'.format(_QuoteValue(default))
  return usage


def _GetInvertedFlagName(flag):
  """Returns the inverted flag name for flag."""
  return flag.option_strings[0].replace('--', '--no-', 1)


def GetArgDetails(arg):
  """Returns the help message with autogenerated details for arg."""
  help_message = arg.help() if callable(arg.help) else arg.help
  help_message = textwrap.dedent(help_message) if help_message else ''
  if arg.is_hidden:
    return help_message
  if arg.is_group or arg.is_positional:
    choices = None
  elif arg.choices:
    choices = arg.choices
  else:
    try:
      choices = arg.type.choices
    except AttributeError:
      choices = None
  extra_help = []
  if hasattr(arg, 'store_property'):
    prop, _, _ = arg.store_property
    # Don't add help if there's already explicit help.
    if str(prop) not in help_message:
      extra_help.append('Overrides the default *{0}* property value'
                        ' for this command invocation.'.format(prop))
      # '?' in Boolean flag check to cover legacy choices={'true', 'false'}
      # flags. They are the only flags with nargs='?'. This would have been
      # much easier if argparse had a first class Boolean flag attribute.
      if prop.default and arg.nargs in (0, '?'):
        extra_help.append('Use *{}* to disable.'.format(
            _GetInvertedFlagName(arg)))
  elif choices:
    metavar = arg.metavar or arg.dest.upper()
    choices = getattr(arg, 'choices_help', choices)
    if len(choices) > 1:
      one_of = 'one of'
    else:
      # TBD I guess?
      one_of = '(currently only one value is supported)'
    if isinstance(choices, dict):
      extra_help.append(
          u'_{metavar}_ must be {one_of}:\n\n{choices}\n\n'.format(
              metavar=metavar,
              one_of=one_of,
              choices='\n'.join(
                  [u'*{name}*::: {desc}'.format(name=name, desc=desc)
                   for name, desc in sorted(choices.iteritems())])))
    else:
      extra_help.append(u'_{metavar}_ must be {one_of}: {choices}.'.format(
          metavar=metavar,
          one_of=one_of,
          choices=', '.join([u'*{0}*'.format(x) for x in choices])))
  elif arg.is_group or arg.is_positional or arg.nargs:
    # Not a Boolean flag.
    pass
  elif arg.default is True:
    extra_help.append(
        'Enabled by default, use *{0}* to disable.'.format(
            _GetInvertedFlagName(arg)))

  if extra_help:
    help_message = help_message.rstrip()
    if help_message:
      extra_help_message = ' '.join(extra_help)
      newline_index = help_message.rfind('\n')
      if newline_index >= 0 and help_message[newline_index + 1] == ' ':
        # Preserve example markdown at end of help_message.
        help_message += '\n\n' + extra_help_message + '\n'
      else:
        if not help_message.endswith('.'):
          help_message += '.'
        if help_message.rfind('\n\n') > 0:
          # help_message has multiple paragraphs. Put extra_help in a new
          # paragraph.
          help_message += '\n\n'
        else:
          help_message += ' '
        help_message += extra_help_message
  return help_message.replace('\n\n', '\n+\n').strip()


def _IsPositional(arg):
  """Returns True if arg is a positional or group that contains a positional."""
  if arg.is_hidden:
    return False
  if arg.is_positional:
    return True
  if arg.is_group:
    for a in arg.arguments:
      if _IsPositional(a):
        return True
  return False


def _GetArgUsageSortKey(name):
  """Arg name usage string key function for sorted."""
  if not name:
    return 0, ''  # paranoid fail safe check -- should not happen
  elif name.startswith('--no-'):
    return 3, name[5:], 'x'  # --abc --no-abc
  elif name.startswith('--'):
    return 3, name[2:]
  elif name.startswith('-'):
    return 4, name[1:]
  elif name[0].isalpha():
    return 1, ''  # stable sort for positionals
  else:
    return 5, name


def GetSingleton(args):
  """Returns the single non-hidden arg in args.arguments or None."""
  singleton = None
  for arg in args.arguments:
    if arg.is_hidden:
      continue
    if arg.is_group:
      arg = GetSingleton(arg)
      if not arg:
        return None
    if singleton:
      return None
    singleton = arg
  if args.is_required and not singleton.is_required:
    singleton = copy.copy(singleton)
    singleton.is_required = True
  return singleton


def GetArgSortKey(arg):
  """Arg key function for sorted."""
  name = re.sub(' +', ' ',
                re.sub('[](){}|[]', '',
                       GetArgUsage(arg, value=False, hidden=True) or ''))
  if arg.is_group:
    singleton = GetSingleton(arg)
    if singleton:
      arg = singleton
  if arg.is_group:
    if _IsPositional(arg):
      return 1, ''  # stable sort for positionals
    if arg.is_required:
      return 6, name
    return 7, name
  elif arg.nargs == argparse.REMAINDER:
    return 8, name
  if arg.is_positional:
    return 1, ''  # stable sort for positionals
  if arg.is_required:
    return 2, name
  return _GetArgUsageSortKey(name)


def GetArgUsage(arg, brief=False, definition=False, markdown=False,
                optional=True, top=False, remainder_usage=None, value=True,
                hidden=False):
  """Returns the argument usage string for arg or all nested groups in arg.

  Mutually exclusive args names are separated by ' | ', otherwise ' '.
  Required groups are enclosed in '(...)', otherwise '[...]'. Required args
  in a group are separated from the optional args by ' : '.

  Args:
    arg: The argument to get usage from.
    brief: bool, If True, only display one version of a flag that has
        multiple versions, and do not display the default value.
    definition: bool, Definition list usage if True.
    markdown: bool, Add markdown if True.
    optional: bool, Include optional flags if True.
    top: bool, True if args is the top level group.
    remainder_usage: [str], Append REMAINDER usage here instead of the return.
    value: bool, If true display flag name=value for non-Boolean flags.
    hidden: bool, Include hidden args if True.

  Returns:
    The argument usage string for arg or all nested groups in arg.
  """
  if arg.is_hidden and not hidden:
    return ''
  if arg.is_group:
    singleton = GetSingleton(arg)
    if singleton and (singleton.is_group or
                      singleton.nargs != argparse.REMAINDER):
      arg = singleton
  if not arg.is_group:
    # A single argument.
    if arg.is_positional:
      usage = GetPositionalUsage(arg, markdown=markdown)
    else:
      inverted = not definition and getattr(arg, 'inverted_synopsis', False)
      usage = GetFlagUsage(arg, brief=brief, markdown=markdown,
                           inverted=inverted, value=value)
    if usage and top and not arg.is_required and not usage.startswith('['):
      usage = u'[{}]'.format(usage)
    return usage

  # An argument group.
  sep = ' | ' if arg.is_mutex else ' '
  positional_args = []
  required_usage = []
  optional_usage = []
  if remainder_usage is None:
    include_remainder_usage = True
    remainder_usage = []
  else:
    include_remainder_usage = False
  for a in sorted(arg.arguments, key=GetArgSortKey):
    if (a.is_hidden or a.help == argparse.SUPPRESS) and not hidden:
      continue
    if a.is_group:
      singleton = GetSingleton(a)
      if singleton:
        a = singleton
    if not a.is_group and a.nargs == argparse.REMAINDER:
      remainder_usage.append(
          GetArgUsage(a, markdown=markdown, value=value, hidden=hidden))
    elif _IsPositional(a):
      positional_args.append(a)
    else:
      usage = GetArgUsage(a, markdown=markdown, value=value, hidden=hidden)
      if not usage:
        continue
      if a.is_required:
        if usage not in required_usage:
          required_usage.append(usage)
      else:
        if top:
          usage = u'[{}]'.format(usage)
        if usage not in optional_usage:
          optional_usage.append(usage)
  all_usage = []
  if positional_args:
    nesting = 0
    for a in positional_args:
      usage = GetArgUsage(a, markdown=markdown, hidden=hidden)
      if not usage:
        continue
      if not a.is_required and not usage.startswith('['):
        usage = u'[{}'.format(usage)
        nesting += 1
      all_usage.append(usage)
    if nesting:
      all_usage[-1] = u'{}{}'.format(all_usage[-1], ']' * nesting)
  if required_usage:
    all_usage.append(sep.join(required_usage))
  if optional_usage:
    if optional:
      if not top and required_usage:
        all_usage.append(':')
      all_usage.append(sep.join(optional_usage))
    elif brief and top:
      all_usage.append('[optional flags]')
  if brief:
    all_usage = sorted(all_usage, key=_GetArgUsageSortKey)
  if remainder_usage and include_remainder_usage:
    all_usage.append(' '.join(remainder_usage))
  usage = ' '.join(all_usage)
  if arg.is_required:
    return u'({})'.format(usage)
  if top or len(all_usage) <= 1:
    return usage
  return u'[{}]'.format(usage)


def GetFlags(arg, optional=False):
  """Returns the list of all flags in arg.

  Args:
    arg: The argument to get flags from.
    optional: Do not include required flags if True.

  Returns:
    The list of all/optional flags in arg.
  """
  flags = set()
  if optional:
    flags.add('--help')

  def _GetFlagsHelper(arg):
    """GetFlags() helper that adds to flags."""
    if arg.is_hidden:
      return
    if arg.is_group:
      for arg in arg.arguments:
        _GetFlagsHelper(arg)
    else:
      show_inverted = getattr(arg, 'show_inverted', None)
      if show_inverted:
        arg = show_inverted
      if (arg.option_strings and
          not arg.is_positional and
          not arg.is_global and
          (not optional or (
              not getattr(arg, 'is_required', False) and
              not getattr(arg, 'required', False)))):
        flags.add(sorted(arg.option_strings)[0])

  _GetFlagsHelper(arg)
  return sorted(flags, key=_GetArgUsageSortKey)


def _GetArgHeading(category):
  """Returns the arg section heading for an arg category."""
  if category is None:
    category = 'OTHER'
  elif 'ARGUMENTS' in category or 'FLAGS' in category:
    return category
  return category + ' FLAGS'


class Section(object):
  """A positional/flag section.

  Attribute:
    heading: str, The section heading.
    args: [Argument], The sorted list of args in the section.
  """

  def __init__(self, heading, args):
    self.heading = heading
    self.args = args


def GetArgSections(arguments, is_root):
  """Returns the positional/flag sections in document order.

  Args:
    arguments: [Flag|Positional], The list of arguments for this command or
      group.
    is_root: bool, True if arguments are for the CLI root command.

  Returns:
    ([Section] global_flags)
      global_flags - The sorted list of global flags if command is not the root.
  """
  categories = {}
  dests = set()
  global_flags = set()
  for arg in arguments:
    if arg.is_hidden:
      continue
    if _IsPositional(arg):
      category = 'POSITIONAL ARGUMENTS'
      if category not in categories:
        categories[category] = []
      categories[category].append(arg)
      continue
    if arg.is_global and not arg.is_hidden and not is_root:
      for a in arg.arguments if arg.is_group else [arg]:
        if a.option_strings and not a.is_hidden:
          flag = a.option_strings[0]
          if flag.startswith('--'):
            global_flags.add(flag)
      continue
    if arg.is_required:
      category = 'REQUIRED'
    else:
      category = getattr(arg, 'category', None) or 'OTHER'
    if hasattr(arg, 'dest'):
      if arg.dest in dests:
        continue
      dests.add(arg.dest)
    if category not in categories:
      categories[category] = set()
    categories[category].add(arg)

  # Collect the priority sections first in order:
  #   POSITIONAL ARGUMENTS, REQUIRED, COMMON, OTHER, and categorized.
  sections = []
  if is_root:
    common = 'GLOBAL'
  else:
    common = base.COMMONLY_USED_FLAGS
  other_flags_heading = 'FLAGS'
  for category, other in (('POSITIONAL ARGUMENTS', ''),
                          ('REQUIRED', 'OPTIONAL'),
                          (common, 'OTHER'),
                          ('OTHER', None)):
    if category not in categories:
      continue
    if other is not None:
      if other:
        other_flags_heading = other
      heading = category
    elif len(categories) > 1:
      heading = 'FLAGS'
    else:
      heading = other_flags_heading
    sections.append(Section(_GetArgHeading(heading),
                            parser_arguments.Argument(
                                arguments=categories[category])))
    # This prevents the category from being re-added in the loop below.
    del categories[category]

  # Add the remaining categories in sorted order.
  for category, args in sorted(categories.iteritems()):
    sections.append(Section(_GetArgHeading(category),
                            parser_arguments.Argument(arguments=args)))

  return sections, global_flags


def WrapWithPrefix(prefix, message, indent, length, spacing, writer=sys.stdout):
  """Helper function that does two-column writing.

  If the first column is too long, the second column begins on the next line.

  Args:
    prefix: str, Text for the first column.
    message: str, Text for the second column.
    indent: int, Width of the first column.
    length: int, Width of both columns, added together.
    spacing: str, Space to put on the front of prefix.
    writer: file-like, Receiver of the written output.
  """
  def W(s):
    writer.write(s)
  def Wln(s):
    W(s + '\n')

  # Reformat the message to be of rows of the correct width, which is what's
  # left-over from length when you subtract indent. The first line also needs
  # to begin with the indent, but that will be taken care of conditionally.
  message = ('\n%%%ds' % indent % ' ').join(
      textwrap.TextWrapper(break_on_hyphens=False, width=length - indent).wrap(
          message.replace(' | ', '&| '))).replace('&|', ' |')
  if len(prefix) > indent - len(spacing) - 2:
    # If the prefix is too long to fit in the indent width, start the message
    # on a new line after writing the prefix by itself.
    Wln('%s%s' % (spacing, prefix))
    # The message needs to have the first line indented properly.
    W('%%%ds' % indent % ' ')
    Wln(message)
  else:
    # If the prefix fits comfortably within the indent (2 spaces left-over),
    # print it out and start the message after adding enough whitespace to make
    # up the rest of the indent.
    W('%s%s' % (spacing, prefix))
    Wln('%%%ds %%s'
        % (indent - len(prefix) - len(spacing) - 1)
        % (' ', message))


def GetUsage(command, argument_interceptor):
  """Return the command Usage string.

  Args:
    command: calliope._CommandCommon, The command object that we're helping.
    argument_interceptor: parser_arguments.ArgumentInterceptor, the object that
      tracks all of the flags for this command or group.

  Returns:
    str, The command usage string.
  """
  command.LoadAllSubElements()
  command_path = ' '.join(command.GetPath())
  topic = len(command.GetPath()) >= 2 and command.GetPath()[1] == 'topic'
  command_id = 'topic' if topic else 'command'

  buf = StringIO.StringIO()

  buf.write('Usage: ')

  usage_parts = []

  if not topic:
    usage_parts.append(GetArgUsage(argument_interceptor, brief=True,
                                   optional=False, top=True))

  group_helps = command.GetSubGroupHelps()
  command_helps = command.GetSubCommandHelps()

  groups = sorted([name for (name, help_info) in group_helps.iteritems()
                   if command.IsHidden() or not help_info.is_hidden])
  commands = sorted([name for (name, help_info) in command_helps.iteritems()
                     if command.IsHidden() or not help_info.is_hidden])

  all_subtypes = []
  if groups:
    all_subtypes.append('group')
  if commands:
    all_subtypes.append(command_id)
  if groups or commands:
    usage_parts.append('<%s>' % ' | '.join(all_subtypes))
    optional_flags = None
  else:
    optional_flags = GetFlags(argument_interceptor, optional=True)

  usage_msg = ' '.join(usage_parts)

  non_option = u'{command} '.format(command=command_path)

  buf.write(non_option + usage_msg + '\n')

  if groups:
    WrapWithPrefix('group may be', ' | '.join(
        groups), HELP_INDENT, LINE_WIDTH, spacing='  ', writer=buf)
  if commands:
    WrapWithPrefix('%s may be' % command_id, ' | '.join(
        commands), HELP_INDENT, LINE_WIDTH, spacing='  ', writer=buf)
  if optional_flags:
    WrapWithPrefix('optional flags may be', ' | '.join(optional_flags),
                   HELP_INDENT, LINE_WIDTH, spacing='  ', writer=buf)

  buf.write(u"""
For detailed information on this command and its flags, run:
  {command_path} --help
""".format(command_path=' '.join(command.GetPath())))

  return buf.getvalue()


def ExtractHelpStrings(docstring):
  """Extracts short help and long help from a docstring.

  If the docstring contains a blank line (i.e., a line consisting of zero or
  more spaces), everything before the first blank line is taken as the short
  help string and everything after it is taken as the long help string. The
  short help is flowing text with no line breaks, while the long help may
  consist of multiple lines, each line beginning with an amount of whitespace
  determined by dedenting the docstring.

  If the docstring does not contain a blank line, the sequence of words in the
  docstring is used as both the short help and the long help.

  Corner cases: If the first line of the docstring is empty, everything
  following it forms the long help, and the sequence of words of in the long
  help (without line breaks) is used as the short help. If the short help
  consists of zero or more spaces, None is used instead. If the long help
  consists of zero or more spaces, the short help (which might or might not be
  None) is used instead.

  Args:
    docstring: The docstring from which short and long help are to be taken

  Returns:
    a tuple consisting of a short help string and a long help string

  """
  if docstring:
    unstripped_doc_lines = docstring.splitlines()
    stripped_doc_lines = [s.strip() for s in unstripped_doc_lines]
    try:
      empty_line_index = stripped_doc_lines.index('')
      short_help = ' '.join(stripped_doc_lines[:empty_line_index])
      raw_long_help = '\n'.join(unstripped_doc_lines[empty_line_index + 1:])
      long_help = textwrap.dedent(raw_long_help).strip()
    except ValueError:  # no empty line in stripped_doc_lines
      short_help = ' '.join(stripped_doc_lines).strip()
      long_help = ''
    if not short_help:  # docstring started with a blank line
      short_help = ' '.join(stripped_doc_lines[empty_line_index + 1:]).strip()
      # words of long help as flowing text
    return (short_help, long_help or short_help)
  else:
    return ('', '')
