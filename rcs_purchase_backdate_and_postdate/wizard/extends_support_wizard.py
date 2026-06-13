from odoo import api, fields, models, _
from odoo.modules.module import load_manifest
from odoo.exceptions import UserError
import requests


class ExtendsSupportWizard(models.TransientModel):
    _name = 'extends.support.wizard'
    _description = 'Support Extension Wizard'

    user_name = fields.Char(string="Name", required=True)
    company_name = fields.Char(
        string="Company",
        default=lambda self: self.env.company.name,
        readonly=True
    )
    contact = fields.Char(string="Mobile", required=True)
    email = fields.Char(string="Email", required=True)

    company_phone = fields.Char(
        string="Company Phone",
        default=lambda self: self.env.company.phone or self.env.company.mobile,
        readonly=True
    )
    company_email = fields.Char(
        string="Company Email",
        default=lambda self: self.env.company.email,
        readonly=True
    )

    company_street = fields.Char(
        string="Address",
        default=lambda self: self.env.company.street,
        readonly=True
    )
    company_street2 = fields.Char(
        default=lambda self: self.env.company.street2,
        readonly=True
    )
    company_city = fields.Char(
        default=lambda self: self.env.company.city,
        readonly=True
    )
    company_state = fields.Char(
        default=lambda self: self.env.company.state_id.name,
        readonly=True
    )
    company_zip = fields.Char(
        default=lambda self: self.env.company.zip,
        readonly=True
    )
    company_country = fields.Char(
        default=lambda self: self.env.company.country_id.name,
        readonly=True
    )

    app_name = fields.Char(
        readonly=True,
        default=lambda self: self._get_module_info()[2]
    )
    app_version = fields.Char(
        readonly=True,
        default=lambda self: self._get_module_info()[3]
    )
    our_company_name = fields.Char(
        readonly=True,
        default=lambda self: self._get_module_info()[1]
    )
    technical_name = fields.Char(
        readonly=True,
        default=lambda self: self._get_module_info()[0]
    )

    message = fields.Text(
        default="Thanks for purchasing the app. Please fill below details to extend 30 days support."
    )

    @api.model
    def _get_module_info(self):
        module = self._module
        try:
            manifest = load_manifest(module)
            return (
                module,
                manifest.get('author'),
                manifest.get('name'),
                manifest.get('version'),
            )
        except Exception:
            return module, False, False, False

    def action_submit(self):
        self.ensure_one()
        url = 'http://150.129.151.225:8072/support/lead'

        payload = {
            'user_name': self.user_name,
            'contact': self.contact,
            'email': self.email,
            'company_name': self.company_name,
            'company_phone': self.company_phone,
            'company_email': self.company_email,
            'street': self.company_street,
            'street2': self.company_street2,
            'city': self.company_city,
            'state': self.company_state,
            'zip': self.company_zip,
            'country': self.company_country,
            'app_name': self.app_name,
            'app_version': self.app_version,
            'technical_name': self.technical_name,
            'our_company_name': self.our_company_name,
        }

        try:
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            raise UserError(_("Failed to send data: %s") % e)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _(
                    'Your details have been submitted successfully. '
                    'Support has been extended for 30 days.'
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
