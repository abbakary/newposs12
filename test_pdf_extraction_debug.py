#!/usr/bin/env python
"""
Debug script to test extraction with the actual PDF content
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tracker.utils.pdf_text_extractor import parse_invoice_data

# Sample extracted text from the user's provided PDF
sample_text = """Superdoll Trailer Manufacture Co. (T) Ltd.
P.O. Box 16541 DSM, Tel.+255-22-2860930-2863467, Fax +255-22-2865412/3, Email: stm@superdoll-tz.com,Tax ID No.100-199-157, VAT Reg. No.10-0085-15-E
P.O. BOX 15950
A01696
25/10/2025
PI-1765632
BF GOODRICH TYRE
LT265/65R17 116/113S TL
ALL-TERRAIN T/A KO3 LRD
RWL GO
VALVE (1214 TR 414) FOR
CAR TUBELESS TYRES
WHEEL BALANCE ALLOYD
RIMS
WHEEL ALIGNMENT SMALL
1
2
3
4
2132004135
3373119002
21004
21019
PCS
PCS
PCS
UNT
Sr
No.
Item Code Description 
Proforma Invoice
Code No
Customer Name STATEOIL TANZANIA LIMITED
Address
Tel Fax
Del. Date
PI No.
Date
Cust Ref
Ref Date
Authorised Signatory
25/10/2025
DAR ES SALAAM
TANZANIA
4
4
4
1
Qty
Kind Attn Valued Customer
Reference
 1,037,400.00
 1,300.00
 12,712.00
 50,848.00
Rate
 3,402,672.00
 5,200.00
 50,848.00
 25,424.00
Value
Payment
Delivery
Net Value
Type 
 3,484,144.00
 18.00%
 50.00%
ex-stock
Cash/Chq on Delivery
Attended By Sales Point
Remarks Looking forward to your conformed order
NOTE 1 : Payment in TSHS accepted at the prevailing rate on the date of payment.
2 : Proforma Invoice is Valid for 2 weeks from date of Proforma.
3 : Discount is Valid only for the above Quantity.
TSH TSH
Gross Value
VAT 627,145.92
TSH 4,111,289.92
:
:
:
: :
:
:
:
:
:
:
:
:
Dear Sir/Madam,
We thank you for your valued enquiry. As desired please find below our detailed best offer
:
:
:
:
:
:
FOR T 290 EFQ
4 : Duty and VAT exemption documents to be submitted with the Purchase Order. FRM-STM-SAL-01A"""

# Parse the invoice data
result = parse_invoice_data(sample_text)

# Display results
print("=" * 70)
print("INVOICE EXTRACTION TEST - DEBUGGING")
print("=" * 70)

print("\n--- HEADER INFORMATION ---")
print(f"Invoice No (PI No): {result['invoice_no']}")
print(f"Code No: {result['code_no']}")
print(f"Date: {result['date']}")
print(f"Customer Name: {result['customer_name']}")
print(f"Address: {result['address']}")
print(f"Phone: {result['phone']}")
print(f"Email: {result['email']}")
print(f"Reference: {result['reference']}")

print("\n--- MONETARY AMOUNTS ---")
print(f"Subtotal (Net Value): {result['subtotal']}")
print(f"Tax (VAT): {result['tax']}")
print(f"Total (Gross Value): {result['total']}")

print("\n--- ADDITIONAL FIELDS ---")
print(f"Payment Method: {result['payment_method']}")
print(f"Delivery Terms: {result['delivery_terms']}")
print(f"Remarks: {result['remarks']}")
print(f"Attended By: {result['attended_by']}")
print(f"Kind Attention: {result['kind_attention']}")

print("\n--- LINE ITEMS ({} items extracted) ---".format(len(result['items'])))
for idx, item in enumerate(result['items'], 1):
    print(f"\nItem {idx}:")
    print(f"  Code: {item.get('code')}")
    print(f"  Description: {item.get('description')}")
    print(f"  Unit: {item.get('unit')}")
    print(f"  Qty: {item.get('qty')}")
    print(f"  Rate: {item.get('rate')}")
    print(f"  Value: {item.get('value')}")

print("\n" + "=" * 70)
print("EXPECTED EXTRACTION RESULTS:")
print("=" * 70)
print("\nCode No: A01696")
print("Customer Name: STATEOIL TANZANIA LIMITED")
print("Address: P.O. BOX 15950 DAR ES SALAAM TANZANIA")
print("Email: stm@superdoll-tz.com")
print("Date: 25/10/2025")
print("PI No: PI-1765632")
print("Reference: FOR T 290 EFQ")

print("\nMonetary:")
print("Subtotal (Net Value): 3484144.00")
print("Tax (VAT): 627145.92")
print("Total (Gross Value): 4111289.92")

print("\nAdditional:")
print("Payment Method: on_delivery (from 'Cash/Chq on Delivery')")
print("Delivery Terms: ex-stock")
print("Remarks: Looking forward to your conformed order")
print("Attended By: Sales Point")
print("Kind Attention: Valued Customer")

print("\nLine Items (4 items expected):")
print("Item 1:")
print("  Code: 2132004135")
print("  Description: BF GOODRICH TYRE LT265/65R17 116/113S TL ALL-TERRAIN T/A KO3 LRD RWL GO")
print("  Unit: PCS")
print("  Qty: 4")
print("  Rate: 1037400.00")
print("  Value: 3402672.00")

print("\nItem 2:")
print("  Code: 3373119002")
print("  Description: VALVE (1214 TR 414) FOR CAR TUBELESS TYRES")
print("  Unit: PCS")
print("  Qty: 4")
print("  Rate: 1300.00")
print("  Value: 5200.00")

print("\nItem 3:")
print("  Code: 21004")
print("  Description: WHEEL BALANCE ALLOYD RIMS")
print("  Unit: PCS")
print("  Qty: 4")
print("  Rate: 12712.00")
print("  Value: 50848.00")

print("\nItem 4:")
print("  Code: 21019")
print("  Description: WHEEL ALIGNMENT SMALL")
print("  Unit: UNT")
print("  Qty: 1")
print("  Rate: 50848.00")
print("  Value: 25424.00")
