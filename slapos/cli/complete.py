# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010-2014 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


import inspect
import argparse
import cliff


class CompleteFish(cliff.complete.CompleteShellBase):
  # not used (we implement the logic in CompleteCommand instead), but registered
  # so that CompleteCommand knows it supports fish output.
  pass


class CompleteCommand(cliff.complete.CompleteCommand):
  """Generate shell completions.
  """
  def take_action(self, parsed_args):
    if parsed_args.shell == 'fish':

      def get_actions(command):
        the_cmd = self.app.command_manager.find_command(command)
        cmd_factory, cmd_name, search_args = the_cmd
        cmd = cmd_factory(self.app, search_args)
        if self.app.interactive_mode:
          full_name = (cmd_name)
        else:
          full_name = (' '.join([self.app.NAME, cmd_name]))
        cmd_parser = cmd.get_parser(full_name)
        return cmd_parser._get_optional_actions()

      def output_action(action, subcommands=()):
        cmd_options = ''
        for option in action.option_strings:
          if option.startswith('--'):
            cmd_options += ' -l {}'.format(option[2:])
          elif option.startswith('-'):
            cmd_options += ' -s {}'.format(option[1:])

        extra_flags = ''
        if isinstance(action, argparse._StoreAction):
          # XXX _StoreAction needs to store *something*, assume it's a file.
          extra_flags = ' -F '

        cmd_description = action.help.replace("'", "\\'")
        subcommand_condition_flag = ''
        if subcommands:
          subcommand_condition = '; and '.join(
            '__fish_seen_subcommand_from {subcommand}'.format(subcommand=subcommand)
            for subcommand in subcommands)

          subcommand_condition_flag = " -n '{subcommand_condition}' ".format(subcommand_condition=subcommand_condition)

        self.app.stdout.write(
          "complete -c {slapos} {subcommand_condition_flag} {extra_flags} {cmd_options} -d '{cmd_description}'\n".format(
              slapos=self.app.NAME,
              subcommand_condition_flag=subcommand_condition_flag,
              extra_flags=extra_flags,
              cmd_options=cmd_options,
              cmd_description=cmd_description,
          )
        )


      self.app.stdout.write("""
# completions for slapos command generated with `slapos complete --shell=fish`

function __fish_print_slapos_services
  echo all\\tAll services
  eval ( commandline -o | head -1 ) node supervisorctl status | sed -e 's/ /\t/'
end

# complete installed softwares for slapos node software --only-sr
function __fish_print_slapos_softwares
  eval ( commandline -o | head -1 ) proxy show --software | tail -n +6 | grep available | awk '{print $4"\\t"$1}'
end
complete -c slapos  -n '__fish_seen_subcommand_from node; and __fish_seen_subcommand_from software; and __fish_contains_opt only-sr only' -f -a '(__fish_print_slapos_softwares)'

# complete busy partitions for slapos node instance --only-cp
function __fish_print_slapos_partitions
  eval ( commandline -o | head -1 ) proxy show --partitions | tail -n +6 | grep busy | awk '{print $1"\\t"$6" "$5" "$4}'
end
complete -c slapos  -n '__fish_seen_subcommand_from node; and __fish_seen_subcommand_from instance; and __fish_contains_opt only-cp only' -f -a '(__fish_print_slapos_partitions)'

""")

      self.app.stdout.write("# all subcommands\n")
      subcommands = set([])
      for subcommand, _ in self.app.command_manager:
        subcommands.add(subcommand.split(' ')[0])
      self.app.stdout.write(
          "set -l __fish_slapos_subcommands {subcommands}\n".format(
              subcommands=' '.join(subcommands)))

      self.app.stdout.write("# general actions\n")
      for action in self.app.parser._get_positional_actions():
        output_action(action)

      subcommands_descriptions = {}
      subcommands_actions = {}
      for cmd_name, _ in self.app.command_manager:
        cmd_class, _, _ = self.app.command_manager.find_command(cmd_name.split())
        cmd_description = (inspect.getdoc(cmd_class) or '').splitlines()[0].replace("'", "\\'")
        subcommands_descriptions[cmd_name] = cmd_description
        subcommands_actions[cmd_name] = get_actions(cmd_name.split())

      subcommands_descriptions.setdefault('cache', 'Manage cache')
      subcommands_descriptions.setdefault('configure', 'Manage configuration')
      subcommands_descriptions.setdefault('computer', 'Manage computer')
      subcommands_descriptions.setdefault('node', 'Manage node')
      subcommands_descriptions.setdefault('proxy', 'Manage proxy')
      subcommands_descriptions.setdefault('service', 'Manage services')

      for cmd_name, cmd_description in sorted(subcommands_descriptions.items()):
        self.app.stdout.write("\n## command {cmd_name}\n".format(cmd_name=cmd_name))

        if ' ' in cmd_name:
          base_cmd, sub_cmd = cmd_name.split(' ')
          other_sub_commands = []
          for other_command in subcommands_actions.keys():
            if ' ' in other_command:
              other_command_base, other_command_cmd = other_command.split()
              if other_command_base == base_cmd:
                other_sub_commands.append(other_command_cmd)
          condition_no_other_subcommand = ' ; and not __fish_seen_subcommand_from '.join(other_sub_commands)

          self.app.stdout.write(
            "complete -c {slapos} -f -n '__fish_seen_subcommand_from {base_cmd} "
            "{condition_no_other_subcommand}' -a '{sub_cmd}' -d '{cmd_description}'\n".format(
                slapos=self.app.NAME,
                base_cmd=base_cmd,
                condition_no_other_subcommand=condition_no_other_subcommand,
                sub_cmd=sub_cmd,
                cmd_description=cmd_description,
            )
          )
        else:
          self.app.stdout.write(
            "complete -c {slapos} -f -n \"not __fish_seen_subcommand_from $__fish_slapos_subcommands\""
            " -a '{cmd_name}' -d '{cmd_description}'\n".format(
                slapos=self.app.NAME,
                cmd_name=cmd_name,
                cmd_description=cmd_description,
            )
          )
        for action in subcommands_actions.get(cmd_name, ()):
          output_action(action, cmd_name.split(' '))

        if cmd_name in (
            'node restart',
            'node start',
            'node status',
            'node stop',
            'node tail',
          ):
          base_cmd, sub_cmd = cmd_name.split(' ')
          self.app.stdout.write(
            "complete -c {slapos} -f "
            " -n '__fish_seen_subcommand_from {base_cmd}; and __fish_seen_subcommand_from {sub_cmd}' "
            " -a '(__fish_print_slapos_services)'\n".format(
                slapos=self.app.NAME,
                base_cmd=base_cmd,
                sub_cmd=sub_cmd,
                cmd_description=cmd_description,
            )
          )
      return

    return super(CompleteCommand, self).take_action(parsed_args)
