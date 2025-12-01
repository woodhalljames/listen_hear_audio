#local db info of problem account causing error

Stripe customer id:
cus_THG7QfK1Sy4zMl
Stripe subscription id: 
sub_1SKhuSDjKIkfYTEmXWTj1JVr
Status:
past_due
Plan id:
price_1SEx2kDjKIkfYTEm87jy0Rpj

"{
  "id": "evt_1SYw8zDjKIkfYTEmPqciXsJ2",
  "object": "event",
  "api_version": "2024-10-28.acacia",
  "created": 1764453445,
  "data": {
    "object": {
      "id": "in_1SVwgyDjKIkfYTEmzKUypFQq",
      "object": "invoice",
      "account_country": "US",
      "account_name": "CACTUS CAT LLC",
      "account_tax_ids": null,
      "amount_due": 1400,
      "amount_overpaid": 0,
      "amount_paid": 0,
      "amount_remaining": 1400,
      "amount_shipping": 0,
      "application": null,
      "application_fee_amount": null,
      "attempt_count": 5,
      "attempted": true,
      "auto_advance": true,
      "automatic_tax": {
        "disabled_reason": null,
        "enabled": false,
        "liability": null,
        "provider": null,
        "status": null
      },
      "automatically_finalizes_at": null,
      "billing_reason": "subscription_cycle",
      "charge": "ch_3SVxe3DjKIkfYTEm2TIeGKdj",
      "collection_method": "charge_automatically",
      "created": 1763740572,
      "currency": "usd",
      "custom_fields": null,
      "customer": "cus_THG7QfK1Sy4zMl",
      "customer_address": null,
      "customer_email": "kstergianopoulos@gmail.com",
      "customer_name": "Κωνσταντινος Στεργιανοπουλος",
      "customer_phone": null,
      "customer_shipping": null,
      "customer_tax_exempt": "none",
      "customer_tax_ids": [],
      "default_payment_method": null,
      "default_source": null,
      "default_tax_rates": [],
      "description": null,
      "discount": null,
      "discounts": [],
      "due_date": null,
      "effective_at": 1763744234,
      "ending_balance": 0,
      "footer": null,
      "from_invoice": null,
      "hosted_invoice_url": "https://invoice.stripe.com/i/acct_1QFevEDjKIkfYTEm/live_YWNjdF8xUUZldkVEaktJa2ZZVEVtLF9UU3NSYzIyUTR5UFRkZWhhZlFaNkZha0FGQ2ZCMFE0LDE1NDk5NDI0OQ0200XxKDtTq6?s=ap",
      "invoice_pdf": "https://pay.stripe.com/invoice/acct_1QFevEDjKIkfYTEm/live_YWNjdF8xUUZldkVEaktJa2ZZVEVtLF9UU3NSYzIyUTR5UFRkZWhhZlFaNkZha0FGQ2ZCMFE0LDE1NDk5NDI0OQ0200XxKDtTq6/pdf?s=ap",
      "issuer": {
        "type": "self"
      },
      "last_finalization_error": null,
      "latest_revision": null,
      "lines": {
        "object": "list",
        "data": [
          {
            "id": "il_1SVwgyDjKIkfYTEmeJwjlG2I",
            "object": "line_item",
            "amount": 1400,
            "amount_excluding_tax": 1400,
            "currency": "usd",
            "description": "1 × Happy Couple (at $14.00 / month)",
            "discount_amounts": [],
            "discountable": true,
            "discounts": [],
            "invoice": "in_1SVwgyDjKIkfYTEmzKUypFQq",
            "livemode": true,
            "metadata": {},
            "parent": {
              "invoice_item_details": null,
              "subscription_item_details": {
                "invoice_item": null,
                "proration": false,
                "proration_details": {
                  "credited_items": null
                },
                "subscription": "sub_1SKhuSDjKIkfYTEmXWTj1JVr",
                "subscription_item": "si_THGRX7p5nukzP5"
              },
              "type": "subscription_item_details"
            },
            "period": {
              "end": 1766332540,
              "start": 1763740540
            },
            "plan": {
              "id": "price_1SEx2kDjKIkfYTEm87jy0Rpj",
              "object": "plan",
              "active": true,
              "aggregate_usage": null,
              "amount": 1400,
              "amount_decimal": "1400",
              "billing_scheme": "per_unit",
              "created": 1759690346,
              "currency": "usd",
              "interval": "month",
              "interval_count": 1,
              "livemode": true,
              "metadata": {},
              "meter": null,
              "nickname": null,
              "product": "prod_T5jEej7jIO5U8E",
              "tiers_mode": null,
              "transform_usage": null,
              "trial_period_days": null,
              "usage_type": "licensed"
            },
            "pretax_credit_amounts": [],
            "price": {
              "id": "price_1SEx2kDjKIkfYTEm87jy0Rpj",
              "object": "price",
              "active": true,
              "billing_scheme": "per_unit",
              "created": 1759690346,
              "currency": "usd",
              "custom_unit_amount": null,
              "livemode": true,
              "lookup_key": null,
              "metadata": {},
              "nickname": null,
              "product": "prod_T5jEej7jIO5U8E",
              "recurring": {
                "aggregate_usage": null,
                "interval": "month",
                "interval_count": 1,
                "meter": null,
                "trial_period_days": null,
                "usage_type": "licensed"
              },
              "tax_behavior": "unspecified",
              "tiers_mode": null,
              "transform_quantity": null,
              "type": "recurring",
              "unit_amount": 1400,
              "unit_amount_decimal": "1400"
            },
            "pricing": {
              "price_details": {
                "price": "price_1SEx2kDjKIkfYTEm87jy0Rpj",
                "product": "prod_T5jEej7jIO5U8E"
              },
              "type": "price_details",
              "unit_amount_decimal": "1400"
            },
            "proration": false,
            "proration_details": {
              "credited_items": null
            },
            "quantity": 1,
            "subscription": "sub_1SKhuSDjKIkfYTEmXWTj1JVr",
            "subscription_item": "si_THGRX7p5nukzP5",
            "tax_amounts": [],
            "tax_rates": [],
            "taxes": [],
            "type": "subscription",
            "unit_amount_excluding_tax": "1400"
          }
        ],
        "has_more": false,
        "total_count": 1,
        "url": "/v1/invoices/in_1SVwgyDjKIkfYTEmzKUypFQq/lines"
      },
      "livemode": true,
      "metadata": {},
      "next_payment_attempt": 1764626241,
      "number": "L4ARUDEI-0002",
      "on_behalf_of": null,
      "paid": false,
      "paid_out_of_band": false,
      "parent": {
        "quote_details": null,
        "subscription_details": {
          "metadata": {},
          "subscription": "sub_1SKhuSDjKIkfYTEmXWTj1JVr"
        },
        "type": "subscription_details"
      },
      "payment_intent": "pi_3SVxe3DjKIkfYTEm2VVrsNuZ",
      "payment_settings": {
        "default_mandate": null,
        "payment_method_options": {
          "acss_debit": null,
          "bancontact": null,
          "card": {
            "request_three_d_secure": "automatic"
          },
          "customer_balance": null,
          "konbini": null,
          "sepa_debit": null,
          "us_bank_account": null
        },
        "payment_method_types": [
          "card"
        ]
      },
      "period_end": 1763740540,
      "period_start": 1761062140,
      "post_payment_credit_notes_amount": 0,
      "pre_payment_credit_notes_amount": 0,
      "quote": null,
      "receipt_number": null,
      "rendering": null,
      "shipping_cost": null,
      "shipping_details": null,
      "starting_balance": 0,
      "statement_descriptor": null,
      "status": "open",
      "status_transitions": {
        "finalized_at": 1763744234,
        "marked_uncollectible_at": null,
        "paid_at": null,
        "voided_at": null
      },
      "subscription": "sub_1SKhuSDjKIkfYTEmXWTj1JVr",
      "subscription_details": {
        "metadata": {}
      },
      "subtotal": 1400,
      "subtotal_excluding_tax": 1400,
      "tax": null,
      "test_clock": null,
      "total": 1400,
      "total_discount_amounts": [],
      "total_excluding_tax": 1400,
      "total_pretax_credit_amounts": [],
      "total_tax_amounts": [],
      "total_taxes": [],
      "transfer_data": null,
      "webhooks_delivered_at": 1763740572
    }
  },
  "livemode": true,
  "pending_webhooks": 1,
  "request": {
    "id": null,
    "idempotency_key": null
  },
  "type": "invoice.payment_failed"
}"