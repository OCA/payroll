# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""Init new fields so existing records keep the historical behaviour."""


def migrate(cr, version):
    if not version:
        return
    # Backfill fixed_value from the historical amount.
    cr.execute(
        """
        UPDATE hr_contract_advantage
        SET fixed_value = amount
        WHERE fixed_value IS NULL OR fixed_value = 0.0
        """
    )
    # Make computation_mode explicit (cover any leftover NULL).
    cr.execute(
        """
        UPDATE hr_contract_advantage
        SET computation_mode = 'fixed'
        WHERE computation_mode IS NULL
        """
    )
    cr.execute(
        """
        UPDATE hr_contract_advantage_template
        SET computation_mode = 'fixed'
        WHERE computation_mode IS NULL
        """
    )
    # Quantity model: default fixed 1.0 -> amount = unit value.
    cr.execute(
        """
        UPDATE hr_contract_advantage
        SET quantity_mode = 'fixed'
        WHERE quantity_mode IS NULL
        """
    )
    cr.execute(
        """
        UPDATE hr_contract_advantage_template
        SET quantity_fixed_value = 1.0
        WHERE quantity_fixed_value IS NULL OR quantity_fixed_value = 0.0
        """
    )
