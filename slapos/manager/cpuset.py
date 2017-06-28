# coding: utf-8
import logging
import math
import os
import os.path
import pwd
import time

from zope import interface as zope_interface
from slapos.manager import interface

logger = logging.getLogger(__name__)


class Manager(object):
  """Manage cgroup's cpuset in terms on initializing and runtime operations.

  CPUSET manager moves PIDs between CPU cores using Linux cgroup system.

  In order to use this feature put "cpuset" into "manager_list" into your slapos
  configuration file inside [slapos] section.

  TODO: there is no limit on number of reserved cores per user.
  """
  zope_interface.implements(interface.IManager)

  cpu_exclusive_file = ".slapos-cpu-exclusive"
  cpuset_path = "/sys/fs/cgroup/cpuset/"
  task_write_mode = "wt"
  config_power_user_option = "power_user_list"

  def __init__(self, config):
    """Retain access to dict-like configuration."""
    self.config = config

  def software(self, software):
    """We don't need to mingle with software."""
    pass

  def format(self, computer):
    """Create cgroup folder per-CPU with exclusive access to the CPU.

    - Those folders are "/sys/fs/cgroup/cpuset/cpu<N>".
    """
    if not os.path.exists("/sys/fs/cgroup/cpuset/cpuset.cpus"):
      logger.warning("CPUSet Manager cannot format computer because cgroups do not exist.")
      return 

    def create_cpuset_subtree(name, cpu_id_list):
      """Create root for cpuset with per-CPU folders."""
      if not cpu_id_list:
        logger.warning("Too less cores - cannot reserve any for \"{}\"".format(name))
        return

      root_path = self._prepare_folder(
          os.path.join(self.cpuset_path, name))
      with open(root_path + "/cpuset.cpus", "wt") as fx:
          # this cgroup manages all `name` cpus
          if len(cpu_id_list) == 1:
            fx.write(str(cpu_id_list[0]))
          else:
            fx.write("{:d}-{:d}".format(cpu_id_list[0], cpu_id_list[-1]))

    create_cpuset_subtree("shared", self._shared_cpu_id_list())
    create_cpuset_subtree("exclusive", self._exclusive_cpu_id_list())
    # separate CPUs in exclusive set
    exclusive_cpu_path = os.path.join(self.cpuset_path, "exclusive")
    write_file("1", exclusive_cpu_path + "/cpuset.cpu_exclusive") # exclusive
    write_file("0", exclusive_cpu_path + "/cpuset.mems")  # it doesn't work without that
    for cpu in self._exclusive_cpu_id_list():
      cpu_path = self._prepare_folder(
        os.path.join(self.cpuset_path, "exclusive", "cpu" + str(cpu)))
      write_file(str(cpu), cpu_path + "/cpuset.cpus") # manage only this cpu
      write_file("1", cpu_path + "/cpuset.cpu_exclusive") # exclusive
      write_file("0", cpu_path + "/cpuset.mems")  # it doesn't work without that


  def instance(self, partition):
    """Control runtime state of the computer."""

    if not os.path.exists(os.path.join(self.cpuset_path, "shared")):
      # check whether the computer was formatted
      logger.warning("CGROUP's CPUSET Manager cannot update computer because it is not cpuset-formatted.")
      return

    request_file = os.path.join(partition.instance_path, self.cpu_exclusive_file)
    if not os.path.exists(request_file) or not read_file(request_file):
      # This instance does not ask for cpu exclusive access
      return

    # Gather list of users allowed to request exlusive cores
    power_user_list = self.config.get(self.config_power_user_option, "").split()
    uid, gid = partition.getUserGroupId()
    uname = pwd.getpwuid(uid).pw_name
    if uname not in power_user_list:
      logger.warning("{} is not allowed to modify cpuset! "
                     "Allowed users are in {} option in config file.".format(
                        uname, self.config_power_user_option))
      return

    # prepare paths to tasks file for all and per-cpu
    tasks_file = os.path.join(self.cpuset_path, "tasks")

    # Gather exclusive CPU usage map {username: set[cpu_id]}
    # We do not need to gather that since we have no limits yet
    #cpu_usage = defaultdict(set)
    #for cpu_id in self._cpu_id_list()[1:]:  # skip the first public CPU
    #  pids = [int(pid)
    #          for pid in read_file(cpu_tasks_file_list[cpu_id]).splitlines()]
    #  for pid in pids:
    #    process = psutil.Process(pid)
    #    cpu_usage[process.username()].add(cpu_id)

    # Move all PIDs from the pool of all CPUs onto shared CPUs.
    running_list = sorted(list(map(int, read_file(tasks_file).split())), reverse=True)
    shared_tasks_path = os.path.join(self.cpuset_path, "shared", "tasks")
    exclusive_tasks_path = os.path.join(self.cpuset_path, "exclusive", "tasks")
    success_set, refused_set = set(), set()
    for pid in running_list:
      try:
        write_file("{:d}\n".format(pid), shared_tasks_path, mode=self.task_write_mode)
        success_set.add(pid)
        time.sleep(0.01)
      except IOError as e:
        refused_set.add(pid)
    logger.debug("Refused to move {:d} PIDs: {!s}\n"
                 "Suceeded in moving {:d} PIDs {!s}\n".format(
                     len(refused_set), refused_set, len(success_set), success_set))

    # Gather all running PIDs for filtering out stale PIDs
    running_pid_set = set(running_list)
    running_pid_set.update(map(int, read_file(shared_tasks_path).split()))

    # Gather already exclusively running PIDs
    exclusive_pid_set = set()
    for cpu_tasks_file in [exclusive_tasks_path, ] + self._exclusive_cpu_tasks_list():
      exclusive_pid_set.update(map(int, read_file(cpu_tasks_file).split()))

    # move processes to their demanded exclusive CPUs
    request_pid_list = map(int, read_file(request_file).split())
    # empty the request file (we will write back only PIDs which weren't moved)
    write_file("", request_file)
    # take such PIDs which are either really running or are not already exclusive
    for request_pid in filter(lambda pid: pid in running_pid_set and pid not in exclusive_pid_set, request_pid_list):
      assigned_cpu = self._move_to_exclusive_cpu(request_pid)
      if assigned_cpu < 0:
        # if no exclusive CPU was assigned - write the PID back and try other time
        write_file("{:d}\n".format(request_pid), request_file, mode="at")

  def _exclusive_cpu_tasks_list(self):
    """Return list of folders for exclusive cpu cores."""
    return [os.path.join(self.cpuset_path, "exclusive", "cpu" + str(cpu_id), "tasks")
            for cpu_id in self._exclusive_cpu_id_list()]
  
  def _shared_cpu_id_list(self):
    """Return list of shared CPU core IDs."""
    cpu_id_list = self._cpu_id_list()
    return cpu_id_list[:int(math.ceil(len(cpu_id_list) / 2))]

  def _exclusive_cpu_id_list(self):
    """Return list of exclusive CPU core IDs."""
    cpu_id_list = self._cpu_id_list()
    return cpu_id_list[int(math.ceil(len(cpu_id_list) / 2)):]

  def _cpu_id_list(self):
    """Extract IDs of available CPUs and return them as a list.

    The first one will be always used for all non-exclusive processes.
    :return: list[int]
    """
    cpu_list = []  # types: list[int]
    with open(self.cpuset_path + "cpuset.cpus", "rt") as cpu_def:
      for cpu_def_split in cpu_def.read().strip().split(","):
        # IDs can be in form "0-4" or "0,1,2,3,4"
        if "-" in cpu_def_split:
          a, b = map(int, cpu_def_split.split("-"))
          cpu_list.extend(range(a, b + 1)) # because cgroup's range is inclusive
          continue
        cpu_list.append(int(cpu_def_split))
    return cpu_list

  def _move_to_exclusive_cpu(self, pid):
    """Try all exclusive CPUs and place the ``pid`` to the first available one.

    :return: int, cpu_id of used CPU, -1 if placement was not possible
    """
    exclusive_cpu_list = self._exclusive_cpu_id_list()
    for exclusive_cpu in exclusive_cpu_list:
      # gather tasks assigned to current exclusive CPU
      task_path = os.path.join(
        self.cpuset_path, "exclusive", "cpu" + str(exclusive_cpu), "tasks")
      task_list = read_file(task_path).split()
      if len(task_list) > 0:
        continue  # skip occupied CPUs
      return self._move_task(pid, exclusive_cpu)[1]
    return -1

  def _move_task(self, pid, cpu_id, cpu_mode="performance"):
    """Move ``pid`` to ``cpu_id``.

    cpu_mode can be "performance" or "powersave"
    """
    known_cpu_mode_list = ("performance", "powersave")
    if cpu_id not in self._exclusive_cpu_id_list():
      raise ValueError("Cannot assign to cpu{:d} because it is shared".format(cpu_id))
    # write the PID into concrete tasks file
    cpu_tasks = os.path.join(self.cpuset_path, "exclusive", "cpu" + str(cpu_id), "tasks")
    write_file("{:d}\n".format(pid), cpu_tasks, mode=self.task_write_mode)
    # set the core to `cpu_mode`
    scaling_governor_file = "/sys/devices/system/cpu/cpu{:d}/cpufreq/scaling_governor".format(cpu_id)
    if os.path.exists(scaling_governor_file):
      if cpu_mode not in known_cpu_mode_list:
        logger.warning("Cannot set CPU to mode \"{}\"! Known modes {!s}".format(
          cpu_mode, known_cpu_mode_list))
      else:
        try:
          with open(scaling_governor_file, self.task_write_mode) as fo:
            fo.write(cpu_mode + "\n")  # default is "powersave"
        except IOError as e:
          # handle permission error
          logger.error("Failed to write \"{}\" to {}".format(cpu_mode, scaling_governor_file))
    return pid, cpu_id

  def _prepare_folder(self, folder):
    """If-Create folder and set group write permission."""
    if not os.path.exists(folder):
      os.mkdir(folder)
      # make your life and testing easier and create mandatory files if they don't exist
      mandatory_file_list = ("tasks", "cpuset.cpus")
      for mandatory_file in mandatory_file_list:
        file_path = os.path.join(folder, mandatory_file)
        if not os.path.exists(file_path):
          with open(file_path, "wb"):
            pass  # touche
    return folder


def read_file(path, mode="rt"):
  with open(path, mode) as fi:
    return fi.read()


def write_file(content, path, mode="wt"):
  try:
    with open(path, mode) as fo:
      fo.write(content)
  except IOError as e:
    logger.error("Cannot write to {}".format(path))
    raise