#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_serialization import jsonutils

from nova import objects
from nova.objects import numa
from nova.scheduler import host_manager
from nova.tests.unit.objects import test_objects
from nova.tests import uuidsentinel as uuids


fake_numa_limit1 = numa.NUMATopologyLimits(cpu_allocation_ratio=1.0,
        ram_allocation_ratio=1.0)
fake_limit1 = {"memory_mb": 1024, "disk_gb": 100, "vcpus": 2,
        "numa_topology": fake_numa_limit1}
fake_limit_obj1 = objects.SchedulerLimits.from_dict(fake_limit1)
fake_host1 = {
        "uuid": uuids.host1,
        "host": "host1",
        "nodename": "node1",
        "cell_uuid": uuids.cell,
        "limits": fake_limit1,
        }
fake_host_state1 = host_manager.HostState("host1", "node1", uuids.cell)
fake_host_state1.uuid = uuids.host1
fake_host_state1.limits = fake_limit1.copy()
fake_alloc1 = {"allocations": [
        {"resource_provider": {"uuid": uuids.host1},
         "resources": {"VCPU": 1,
                       "MEMORY_MB": 1024,
                       "DISK_GB": 100}
        }]}
fake_alloc_version = "1.23"


class _TestSelectionObject(object):
    def test_create_with_values(self):
        json_alloc = jsonutils.dumps(fake_alloc1)
        dest = objects.Selection(service_host="host", nodename="node",
                compute_node_uuid=uuids.host1, cell_uuid=uuids.cell,
                limits=fake_limit_obj1, allocation_request=json_alloc,
                allocation_request_version=fake_alloc_version)
        self.assertEqual("host", dest.service_host)
        self.assertEqual(uuids.host1, dest.compute_node_uuid)
        self.assertEqual("node", dest.nodename)
        self.assertEqual(uuids.cell, dest.cell_uuid)
        self.assertEqual(fake_limit_obj1, dest.limits)
        self.assertEqual(json_alloc, dest.allocation_request)
        self.assertEqual(fake_alloc_version, dest.allocation_request_version)

    def test_passing_dict_allocation_fails(self):
        self.assertRaises(ValueError, objects.Selection, service_host="host",
                compute_node_uuid=uuids.host, nodename="node",
                cell_uuid=uuids.cell, allocation_request=fake_alloc1,
                allocation_request_version=fake_alloc_version)

    def test_passing_numeric_allocation_version_converts(self):
        json_alloc = jsonutils.dumps(fake_alloc1)
        dest = objects.Selection(service_host="host",
                compute_node_uuid=uuids.host, nodename="node",
                cell_uuid=uuids.cell, allocation_request=json_alloc,
                allocation_request_version=1.23)
        self.assertEqual("1.23", dest.allocation_request_version)

    def test_from_host_state(self):
        dest = objects.Selection.from_host_state(fake_host_state1, fake_alloc1,
                fake_alloc_version)
        self.assertEqual(dest.service_host, fake_host_state1.host)
        expected_alloc = jsonutils.dumps(fake_alloc1)
        self.assertEqual(dest.allocation_request, expected_alloc)
        self.assertEqual(dest.allocation_request_version, fake_alloc_version)

    def test_from_host_state_no_alloc_info(self):
        dest = objects.Selection.from_host_state(fake_host_state1)
        self.assertEqual(dest.service_host, fake_host_state1.host)
        expected_alloc = jsonutils.dumps(None)
        self.assertEqual(expected_alloc, dest.allocation_request)
        self.assertIsNone(dest.allocation_request_version)


class TestSelectionObject(test_objects._LocalTest,
                            _TestSelectionObject):
    pass


class TestRemoteSelectionObject(test_objects._RemoteTest,
                                  _TestSelectionObject):
    pass
