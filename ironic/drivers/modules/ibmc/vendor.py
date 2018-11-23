# TODO(bill.chan) license

from oslo_log import log
import requests

from ironic.common import exception
from ironic.common.i18n import _
from ironic.drivers import base
from ironic.drivers.modules.ibmc import utils

LOG = log.getLogger(__name__)


class IBMCVendor(base.VendorInterface):

    def __init__(self):
        """Initialize the iBMC vendor interface."""
        super(IBMCVendor, self).__init__()

    def validate(self, task, method=None, **kwargs):
        """Validate vendor-specific actions.

        If invalid, raises an exception; otherwise returns None.

        :param task: A task from TaskManager.
        :param method: Method to be validated
        :param kwargs: Info for action.
        :raises: UnsupportedDriverExtension if 'method' can not be mapped to
                 the supported interfaces.
        :raises: InvalidParameterValue if kwargs does not contain 'method'.
        :raises: MissingParameterValue
        """
        utils.parse_driver_info(task.node)

    def get_properties(self):
        """Return the properties of the interface.

        :returns: dictionary of <property name>:<property description> entries.
        """
        return utils.COMMON_PROPERTIES.copy()

    @base.passthru(['GET'], async=False,
                   description=_('Returns a dictionary, '
                                 'containing node boot types, '
                                 'in ascending order'))
    def list_boot_type_order(self, task, **kwargs):
        """List boot type order of the node.

        :param task: A TaskManager instance containing the node to act on.
        :param kwargs: Not used.
        :raises: InvalidParameterValue if kwargs does not contain 'method'.
        :raises: MissingParameterValue
        :returns: A dictionary, containing node boot types,
                in ascending order.
        """
        self.validate(task)
        system = utils.get_system(task.node)
        try:
            boot_seq = system.boot_sequence
            return {'boot_type': boot_seq}
        except requests.exceptions.RequestException as e:
            error_msg = (_('IBMC get bootup sequence failed '
                           'for node %(node)s. Error: %(error)s') %
                         {'node': task.node.uuid, 'error': e})
            LOG.error(error_msg)
            raise exception.IBMCError(error=error_msg)
