REST API DESCRIPTION
=====================

The follow text contains the REST API Description for Communication
between slapos.slap and master/proxy.

GET /<computer_id>

  Returns information about computer

POST /<computer_id>/partition/<computer_partition_id>   < connection (json/xml)

  Set instance parameter informations on the slagrid server 

POST /<computer_id>/usage 

  Report computer partition usage 

### SOFTWARE RELEASE WORKFLOW

POST /<computer_id>/software/building

  Reports that Software Release is being build

POST /<computer_id>/software/available

  Reports that Software Release is available

POST /<computer_id>/software/error

  Add an error for a software Release workflow

### Computer Partition Workflow

POST /<computer_id>/partition/<computer_partition_id>/building

  Reports that Computer Partition is being build

POST /<computer_id>/partition/<computer_partition_id>/available

  Reports that Computer Partition is available

POST /<computer_id>/partition/<computer_partition_id>/error

  Add an error for the software Instance Workflow

POST /<computer_id>/partition/<computer_partition_id>/started

  Reports that Computer Partition is started

POST /<computer_id>/partition/<computer_partition_id>/stopped

  Reports that Computer Partition is stopped

POST /<computer_id>/partition/<computer_partition_id>/destroyed

  Reports that Computer Partition is destroyed

### Still undecided

#@app.route('<computer-id>/partition/<partition_reference>', methods=['PUT'])
@app.route('/partition', methods=['POST'])
def requestComputerPartition(partition_reference = ''):

PUT ??? /configuration < json

   Load the given json as configuration for the computer object

GET /<computer_reference>/partition/<partition_reference>

  Registers connected representation of computer partition and
  returns Computer Partition class object ????
