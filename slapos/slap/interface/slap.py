##############################################################################
#
# Copyright (c) 2010, 2011, 2012 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
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
from zope.interface import Interface
from zope.interface import Attribute

"""
Note: all strings accepted/returned by the slap library are encoded in UTF-8.
"""


class IException(Interface):
  """
  Classes which implement IException are used to report errors.
  """


class IConnectionError(IException):
  """
  Classes which implement IServerError are used to report a connection problem
  to the slap server.
  """


class IServerError(IException):
  """
  Classes which implement IServerError are used to report unexpected error
  from the slap server.
  """


class INotFoundError(IException):
  """
  Classes which implement INotFoundError are used to report missing
  information on the slap server.
  """


class IResourceNotReady(IException):
  """
  Classes which implement IResourceNotReady are used to report resource not
  ready on the slap server.
  """


class IRequester(Interface):
  """
  Classes which implement IRequester can request software instance to the
  slapgrid server.
  """

  def request(software_release, software_type, partition_reference,
              shared=False, partition_parameter_kw=None, filter_kw=None):
    """
    Request software release instantiation to slapgrid server.

    Returns a new computer partition document, where this software release will
    be installed.

    software_release -- URI of the software release
                        which has to be instantiated

    software_type -- type of component provided by software_release

    partition_reference -- local reference of the instance used by the recipe
                           to identify the instances.

    shared -- boolean to use a shared service

    partition_parameter_kw -- dictionary of parameter used to fill the
                              parameter dictionary of newly created partition.

    filter_kw -- dictionary of filtering parameter to select the requested
                 computer partition.

      computer_guid - computer of the requested partition
      partition_type - virtio, slave, full, limited
      port - port provided by the requested partition

    Example:
       request('http://example.com/foo/bar', 'typeA', 'mysql_1')
    """

  def getInformation(partition_reference):
    """
    Get information about an existing instance.
    If it is called from a Computer Partition, get information
    about Software Instance of the instance tree.

    partition_reference -- local reference of the instance used by the recipe
                           to identify the instances.
    """


class ISoftwareRelease(Interface):
  """
  Software release interface specification
  """

  def getURI():
    """
    Returns a string representing the URI of the software release.
    """

  def getComputerId():
    """
    Returns a string representing the identifier of the computer where the SR
    is installed.
    """

  def getState():
    """
    Returns a string representing the expected state of the software
    installation.

    The result can be: available, destroyed
    """

  def available():
    """
    Notify (to the slapgrid server) that the software release is
    available.
    """

  def building():
    """
    Notify (to the slapgrid server) that the software release is not
    available and under creation.
    """

  def destroyed():
    """
    Notify (to the slapgrid server) that the software installation has
    been correctly destroyed.
    """

  def error(error_log):
    """
    Notify (to the slapgrid server) that the software installation is
    not available and reports an error.

    error_log -- a text describing the error
                 It can be a traceback for example.
    """


class ISoftwareProductCollection(Interface):
  """
  Fake object representing the abstract of all Software Products.
  Can be used to call "Product().mysoftwareproduct", or, simpler,
  "product.mysoftwareproduct", to get the best Software Release URL of the
  Software Product "mysoftwareproduct".

  Example: product.kvm will have the value of the latest Software
  Release URL of KVM.
  """


class ISoftwareInstance(Interface):
  """
  Classes which implement ISoftwareRelease are used by slap to represent
  information about a Software Instance.
  """


class IComputerPartition(IRequester):
  """
  Computer Partition interface specification

  Classes which implement IComputerPartition can propagate the computer
  partition state to the SLAPGRID server and request new computer partition
  creation.
  """

  def stopped():
    """
    Notify (to the slapgrid server) that the software instance is
    available and stopped.
    """

  def started():
    """
    Notify (to the slapgrid server) that the software instance is
    available and started.
    """

  def destroyed():
    """
    Notify (to the slapgrid server) that the software instance has
    been correctly destroyed.
    """

  def error(error_log):
    """
    Notify (to the slapgrid server) that the software instance is
    not available and reports an error.

    error_log -- a text describing the error
                 It can be a traceback for example.
    """

  def getId():
    """
    Returns a string representing the identifier of the computer partition
    inside the slapgrid server.
    """

  def getInstanceGuid():
    """
    Returns a string representing the unique identifier of the instance
    inside the slapgrid server.
    """

  def getState():
    """
    Returns a string representing the expected state of the computer partition.

    The result can be: started, stopped, destroyed
    """

  def getAccessStatus():
    """Get latest computer partition Access message state"""

  def getSoftwareRelease():
    """
    Returns the software release associate to the computer partition.

    Raise an INotFoundError if no software release is associated.
    """

  def getInstanceParameterDict():
    """
    Returns a dictionary of instance parameters.

    The contained values can be used to fill the software instantiation
    profile.
    """

  def getConnectionParameterDict():
    """
    Returns a dictionary of connection parameters.

    The contained values are connection parameters of a compute partition.
    """

  def getType():
    """
    Returns the Software Type of the instance.
    """

  def setUsage(usage_log):
    """
    Associate a usage log to the computer partition.
    This method does not report the usage to the slapgrid server. See
    IComputer.report.

    usage_log -- a text describing the computer partition usage.
                 It can be an XML for example.
    """

  def bang(log):
    """
    Report a problem detected on a computer partition.
    This will trigger the re-instantiation of all partitions in the instance tree.

    log -- a text explaining why the method was called
    """

  def getCertificate():
    """
    Returns a dictionary containing the authentication certificates
    associated to the computer partition.
    The dictionary keys are:
      key -- value is a SSL key
      certificate -- value is a SSL certificate

    Raise an INotFoundError if no software release is associated.
    """

  def setConnectionDict(connection_dict, slave_reference=None):
    """
    Store the connection parameters associated to a partition.

    connection_dict -- dictionary of parameter used to fill the
                              connection dictionary of the partition.

    slave_reference -- current reference of the slave instance to modify
    """

  def getInstanceParameter(key):
    """
    Returns the instance parameter associated to the key.

    Raise an INotFoundError if no key is defined.

    key -- a string name of the parameter
    """

  def getConnectionParameter(key):
    """
    Return the connection parameter associate to the key.

    Raise an INotFoundError if no key is defined.

    key -- a string name of the parameter
    """

  def rename(partition_reference, slave_reference=None):
    """
    Change the partition reference of a partition

    partition_reference -- new local reference of the instance used by the recipe
                           to identify the instances.

    slave_reference -- current reference of the slave instance to modify
    """

  def getStatus():
    """
    Returns a dictionary containing the latest status of the
    computer partition.
    The dictionary keys are:
      user -- user who reported the latest status
      created_at -- date of the status
      text -- message log of the status
    """

  def getFullHostingIpAddressList():
    """
    Returns a dictionary containing the latest status of the
    computer partition.
    """

  def setComputerPartitionRelatedInstanceList(instance_reference_list):
    """
    Set relation between this Instance and all his children.

    instance_reference_list -- list of instances requested by this Computer
                               Partition.
    """


class IComputer(Interface):
  """
  Computer interface specification

  Classes which implement IComputer can fetch information from the slapgrid
  server to know which Software Releases and Software Instances have to be
  installed.
  """

  def getSoftwareReleaseList():
    """
    Returns the list of software release which has to be supplied by the
    computer.

    Raise an INotFoundError if computer_guid doesn't exist.
    """

  def getComputerPartitionList():
    """
    Returns the list of configured computer partitions associated to this
    computer.

    Raise an INotFoundError if computer_guid doesn't exist.
    """

  def reportUsage(computer_partition_list):
    """
    Report the computer usage to the slapgrid server.
    IComputerPartition.setUsage has to be called on each computer partition to
    define each usage.

    computer_partition_list -- a list of computer partition for which the usage
                               needs to be reported.
    """

  def bang(log):
    """
    Report a problem detected on a computer.
    This will trigger IComputerPartition.bang on all instances hosted by the
    Computer.

    log -- a text explaining why the method was called
    """

  def updateConfiguration(configuration_xml):
    """
    Report the current computer configuration.

    configuration_xml -- computer XML description generated by slapformat
    """

  def getStatus():
    """
    Returns a dictionary containing the latest status of the
    computer.
    The dictionary keys are:
      user -- user who reported the latest status
      created_at -- date of the status
      text -- message log of the status
    """

  def generateCertificate():
    """
    Returns a dictionary containing the new certificate files for
    the computer.
    The dictionary keys are:
      key -- key file
      certificate -- certificate file

    Raise ValueError is another certificate is already valid.
    """

  def revokeCertificate():
    """
    Revoke current computer certificate.

    Raise ValueError is there is not valid certificate.
    """


class IOpenOrder(IRequester):
  """
  Open Order interface specification

  Classes which implement Open Order describe which kind of software instances
  is requested by a given client.
  """

  def requestComputer(computer_reference):
    """
    Request a computer to slapgrid server.

    Returns a new computer document.

    computer_reference -- local reference of the computer
    """


class ISupply(Interface):
  """
  Supply interface specification

  Classes which implement Supply describe which kind of software releases
  a given client is ready to supply.
  """

  def supply(software_release, computer_guid=None, state="available"):
    """
    Request installation or deletion of a software relase.
    To destroy a software, supply it with state "destroyed".

    software_release -- URI of the software release
                        which has to be instantiated

    computer_guid -- the identifier of the computer inside the slapgrid
                     server.

    state -- the state of the software, can be "available" or "destroyed".
    """


class slap(Interface):
  """
  Initialize slap connection to the slapgrid server

  Slapgrid server URL is defined during the slap library installation,
  as recipes should not use another server.
  """

  def initializeConnection(slapgrid_uri, authentification_key=None):
    """
    Initialize the connection parameters to the slapgrid servers.

    slapgrid_uri -- URI the slapgrid server connector

    authentification_key -- string the authenticate the agent. (Yes, there's a typo in the argument name)

    Example: https://slapos.server/slap_interface
    """

  def registerComputer(computer_guid):
    """
    Instantiate a computer in the slap library.

    computer_guid -- the identifier of the computer inside the slapgrid server.
    """

  def registerComputerPartition(computer_guid, partition_id):
    """
    Instantiate a computer partition in the slap library.

    computer_guid -- the identifier of the computer inside the slapgrid server.

    partition_id -- the identifier of the computer partition inside the
                    slapgrid server.

    Raise an INotFoundError if computer_guid doesn't exist.
    """

  def registerSoftwareRelease(software_release):
    """
    Instantiate a software release in the slap library.

    software_release -- URI of the software release definition
    """

  def registerOpenOrder():
    """
    Instantiate an open order in the slap library.
    """

  def registerSupply():
    """
    Instantiate a supply in the slap library.
    """

  def getSoftwareReleaseListFromSoftwareProduct(software_product_reference, software_release_url):
    """
    Get the list of Software Releases from a product or from another related
    Software Release, from a Software Product point of view.
    """

  def getOpenOrderDict():
    """
    Get the list of existing open orders (services) for the current user.
    """


class IStandaloneSlapOS(ISupply, IRequester):
  """A SlapOS that can be embedded in other applications,
  also useful for testing.

  This plays the role of an `IComputer` where users of classes
  implementing this interface can install software, create partitions
  and access parameters of the running partitions.

  Extends the existing `IRequester` and `ISupply`, with the
  special behavior that `IRequester.request` and `ISupply.supply` will
  automatically use the embedded computer.
  """

  def __init__(base_directory, server_ip, server_port):
    """Constructor, just create an instance in `base_directory`.

    Arguments:
      * `base_directory`  -- the directory which will contain softwares and instances.
      * `server_ip`, `server_port` -- the address this SlapOS proxy will listen to.

    Error cases:
      * `IException` when `base_directory` is too deep. Because of limitation with
        the length of paths of UNIX sockets, too deep paths cannot be used. Note that
        once slapns work is integrated, this should not be an issue anymore.
    """

  def register():
    """Creates configuration file, starts the SlapOS proxy. TODO ?

        Error cases:
          * `socket.SocketError` when failed to bind `server_ip` / `server_port`.
             SlapOS proxy might already be running.
    """

  def simple_format(partition_count, ipv4_address, ipv6_address):
    """Creates `partition_count` partitions.

    All partitions are created to listen on `ipv4_address` and `ipv6_address`.

    Stop and delete previously existing instances. XXX ???
    Error when already running.

    This is a simplified version of format that uses current user and
    same ips for all partitions.
    """

  def getInstallProcess():
    """Returns a IStandaloneSlapOSProcess installing softwares.
    """

  def getInstanciationProcess():
    """Returns a IStandaloneSlapOSProcess creating instances.
    """

  def getReportProcess():
    """ XXX Name? Cleanup unused instances."""

  def getComputerPartition(partition_reference):
    """Returns the `IComputerPartition` for partition with reference `partition_reference`
    """

  def getComputer():
    """ XXX do we need need getPartition?
    """

  def shutdown():
    """Stop embedded SlapOS server and running instances.
    """

  def cleanup():
    """Remove instances and softwares.

    In most cases, this method is not recommended because it's
    usually convenient to keep softwares installed.
    XXX bad idea ? this is just .shutdown() the shutil.rmtree ?
    """


class IStandaloneSlapOSProcess(Interface):
  """A background process.  XXX more doc
  """
  return_code = Attribute("""Return code of the process.
  None if process is still running or was killed. ( XXX why no return code if killed ?)
  """)
  output = Attribute("""output of the program.""")

  def start():
    """Start the process.

    Returns immediately.
    """

  def isAlive():
    """Returns True if process is still alive, false otherwise.
    Returns immediately.
    """

  def terminate():
    """Stop the process.
    Must call join() after terminate.
    """

  def join():
    """Wait until process finished.
    """


class ISynchronousStandaloneSlapOS(IStandaloneSlapOS):
  """A synchronous API on top of IStandaloneSlapOS, for convenience
  """
  def installSoftware(max_retry=0, debug=False):
    """Synchronously install or uninstall all softwares previously supplied/removed.

    This method retries on errors. If after `max_retry` times there's
    still an error, the error is raised.

    Error cases:
      * `IException` when buildout error while installing software.
      * Unexpected `IConnectionError` while connecting embedded slap server.
    """

  def instantiatePartition(max_retry=5):
    """Instantiate all partitions previously requested.

    This method retry on errors. If after `max_retry` times there's
    still an error, the error is raised.

    Error cases:
      * `IResourceNotReady` requested software_url is not installed.
      * `IException` when buildout error while installing software.
        In that case, exception message contain the last lines of the
        buildout log to help diagnosing what the problem was.
      * `IException` when some promise are reporting errors.
      * Unexpected `IConnectionError` while connecting embedded slap server.
    """
