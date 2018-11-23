# TODO(bill.chan) license

import mock

from ironic.conductor import task_manager
from ironic.drivers.modules.ibmc import utils
from ironic.tests.unit.db import base as db_base
from ironic.tests.unit.db import utils as db_utils
from ironic.tests.unit.objects import utils as obj_utils

INFO_DICT = db_utils.get_test_ibmc_info()


@mock.patch('eventlet.greenthread.sleep', lambda _t: None)
class IBMCVendorTestCase(db_base.DbTestCase):

    def setUp(self):
        super(IBMCVendorTestCase, self).setUp()
        self.config(enabled_hardware_types=['ibmc'],
                    enabled_power_interfaces=['ibmc'],
                    enabled_management_interfaces=['ibmc'],
                    enabled_vendor_interfaces=['ibmc'])
        self.node = obj_utils.create_test_node(
            self.context, driver='ibmc', driver_info=INFO_DICT)

    def test_get_properties(self):
        with task_manager.acquire(self.context, self.node.uuid,
                                  shared=True) as task:
            properties = task.driver.get_properties()
            for prop in utils.COMMON_PROPERTIES:
                self.assertIn(prop, properties)

    @mock.patch.object(utils, 'parse_driver_info', autospec=True)
    def test_validate(self, mock_parse_driver_info):
        with task_manager.acquire(self.context, self.node.uuid,
                                  shared=True) as task:
            task.driver.power.validate(task)
            mock_parse_driver_info.assert_called_once_with(task.node)

    @mock.patch('ironic.drivers.modules.ibmc.utils.IBMCSystem.bios',
                new_callable=mock.PropertyMock)
    @mock.patch.object(utils, 'get_system', autospec=True)
    def test_list_boot_type_order(self, mock_get_system, mock_bios):
        bios_attrs = {
            'Other': 'asdf',
            'BootTypeOrder0': 'PXE',
            'BootTypeOrder1': 'HardDiskDrive',
            'BootTypeOrder3': 'Others',
            'BootTypeOrder2': 'DVDROMDrive',
        }
        fake_system = mock.MagicMock()
        mock_bios.return_value = bios_attrs
        type(fake_system).bios = mock_bios
        mock_get_system.return_value = fake_system

        keys = sorted(bios_attrs.keys())
        sorted_orders = [bios_attrs.get(k) for k in keys
                         if k.lower().startswith('boottypeorder')]
        expected = ', '.join(sorted_orders)
        with task_manager.acquire(self.context, self.node.uuid,
                                  shared=True) as task:
            boot_type_orders = task.driver.vendor.list_boot_type_order(task)
            mock_get_system.assert_called_once_with(task.node)
            mock_bios.assert_called_once_with()
            self.assertEqual(expected, boot_type_orders)
