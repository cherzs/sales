from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None



class AccountMove(models.Model):
    _inherit = 'account.move'



    def _amount_to_text(self):
        self.ensure_one()
        amount = self.amount_total
        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        integral, _sep, fractional = f"{amount:.{self.currency_id.decimal_places}f}".partition('.')
        integer_value = int(integral)
        if self.currency_id.is_zero(amount - integer_value):
            amount_to_text =  _(
                '%(integral_amount)s %(currency_unit)s',
                integral_amount=_num2words(integer_value, lang='id'),
                currency_unit=self.currency_id.currency_unit_label,
            )
        else:
            amount_to_text = _(
                '%(integral_amount)s %(currency_unit)s and %(fractional_amount)s %(currency_subunit)s',
                integral_amount=_num2words(integer_value, lang='id'),
                currency_unit=self.currency_id.currency_unit_label,
                fractional_amount=_num2words(int(fractional or 0), lang='id'),
                currency_subunit=self.currency_id.currency_subunit_label,
            )
        
        
        
        return amount_to_text
        

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'



    def _get_label_without_product_code(self):
        self.ensure_one()
        current_name = self.name or ""
        product_display_name = self.product_id.display_name or ""

        if not current_name:
            return ""
        if not product_display_name:
            return current_name

        if product_display_name in current_name:
            if hasattr(self.product_id, '_get_display_name_without_code'):
                return current_name.replace(
                    product_display_name,
                    self.product_id._get_display_name_without_code() or ""
                )

            if self.product_id.default_code:
                code_pattern = f"[{self.product_id.default_code}] "
                return current_name.replace(code_pattern, "")

        return current_name