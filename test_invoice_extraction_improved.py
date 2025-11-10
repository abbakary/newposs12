#!/usr/bin/env python
"""
Test script to validate improved invoice extraction for the Superdoll invoice format.
Tests that line items are properly extracted with correct descriptions, quantities, and values.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tracker.utils.pdf_text_extractor import parse_invoice_data
from decimal import Decimal

# Test text simulating PyMuPDF extraction of the Superdoll PI-1765632 invoice
superdoll_text = """Superdoll Trailer Manufacture Co. (T) Ltd.
P.O. Box 16541 DSM, Tel.+255-22-2860930-2863467, Fax +255-22-2865412/3, Email: stm@superdoll-tz.com,Tax ID No.100-199-157, VAT Reg. No.10-0085-15-E

Proforma Invoice

Code No : A01696
Customer Name : STATEOIL TANZANIA LIMITED
Address
P.O.BOX 15950
DAR ES SALAAM
TANZANIA

Tel :
Fax :
Del. Date : 25/10/2025
PI No. : PI-1765632
Date : 25/10/2025
Cust Ref :
Ref Date :
Attended By : Sales Point
Kind Attention : Valued Customer
Reference : FOR T 290 EFQ

Sr Item Code Description Type Qty Rate TSH Value TSH
No.
1 2132004135 BF GOODRICH TYRE 4 PCS 1,037,400.00 3,402,672.00
LT265/65R17 116/113S TL 18.00%
ALL-TERRAIN T/A KO3 LRD
RWL GO

2 3373119002 VALVE (1214 TR 414) FOR 4 PCS 1,300.00 5,200.00
CAR TUBELESS TYRES

3 21004 WHEEL BALANCE ALLOYD 4 PCS 12,712.00 50,848.00
RIMS

4 21019 WHEEL ALIGNMENT SMALL 1 UNT 50,848.00 25,424.00
50.00%

Net Value : TSH 3,484,144.00
VAT : TSH 627,145.92
Gross Value : TSH 4,111,289.92

Payment : Cash/Chq on Delivery
Delivery : ex-stock
Remarks : Looking forward to your conformed order

NOTE 1 : Payment in TSHS accepted at the prevailing rate on the date of payment.
2 : Proforma Invoice is Valid for 2 weeks from date of Proforma.
3 : Discount is Valid only for the above Quantity.
4 : Duty and VAT exemption documents to be submitted with the Purchase Order.

Authorised Signatory
FRM-STM-SAL-01A
"""

def test_extraction():
    """Test the extraction and print detailed results"""
    print("=" * 80)
    print("TESTING IMPROVED INVOICE EXTRACTION")
    print("=" * 80)
    
    result = parse_invoice_data(superdoll_text)
    
    # Test 1: Header Information
    print("\n1. HEADER INFORMATION")
    print("-" * 80)
    print(f"Invoice No (PI No): {result['invoice_no']}")
    print(f"Code No: {result['code_no']}")
    print(f"Date: {result['date']}")
    print(f"Customer Name: {result['customer_name']}")
    print(f"Address: {result['address']}")
    
    # Verify header
    assert result['invoice_no'] == 'PI-1765632', f"Expected PI-1765632, got {result['invoice_no']}"
    assert result['code_no'] == 'A01696', f"Expected A01696, got {result['code_no']}"
    assert result['customer_name'] == 'STATEOIL TANZANIA LIMITED', f"Expected STATEOIL TANZANIA LIMITED, got {result['customer_name']}"

    # Verify address contains all expected components
    address = result['address'] or ''
    assert 'P.O.BOX 15950' in address or 'P.O BOX 15950' in address or '15950' in address, \
        f"Address should contain P.O.BOX 15950, got: {address}"
    assert 'DAR' in address or 'SALAAM' in address, \
        f"Address should contain DAR or SALAAM, got: {address}"
    assert 'TANZANIA' in address, \
        f"Address should contain TANZANIA, got: {address}"

    print(f"Address extracted: {address}")
    print("✓ PASS: Header information correct")
    
    # Test 2: Monetary Amounts
    print("\n2. MONETARY AMOUNTS")
    print("-" * 80)
    print(f"Subtotal (Net Value): {result['subtotal']}")
    print(f"Tax/VAT: {result['tax']}")
    print(f"Total (Gross Value): {result['total']}")
    
    # Verify amounts
    assert result['subtotal'] == Decimal('3484144'), f"Subtotal should be 3484144, got {result['subtotal']}"
    assert result['tax'] == Decimal('627145.92'), f"Tax should be 627145.92, got {result['tax']}"
    assert result['total'] == Decimal('4111289.92'), f"Total should be 4111289.92, got {result['total']}"
    print("✓ PASS: Monetary amounts correct")
    
    # Test 3: Line Items
    print("\n3. LINE ITEMS")
    print("-" * 80)
    print(f"Total items extracted: {len(result['items'])}")
    
    assert len(result['items']) == 4, f"Expected 4 items, got {len(result['items'])}"
    
    for i, item in enumerate(result['items'], 1):
        print(f"\nItem {i}:")
        print(f"  Description: {item['description']}")
        print(f"  Code: {item['code']}")
        print(f"  Qty: {item['qty']}")
        print(f"  Unit: {item['unit']}")
        print(f"  Rate: {item['rate']}")
        print(f"  Value: {item['value']}")
    
    # Verify specific items
    item1 = result['items'][0]
    assert 'BF GOODRICH TYRE' in item1['description'], f"Item 1 description should mention 'BF GOODRICH TYRE', got: {item1['description']}"
    assert item1['code'] == '2132004135', f"Item 1 code should be 2132004135, got {item1['code']}"
    assert item1['qty'] == 4, f"Item 1 qty should be 4, got {item1['qty']}"
    assert item1['unit'] == 'PCS', f"Item 1 unit should be PCS, got {item1['unit']}"
    assert item1['value'] == Decimal('3402672'), f"Item 1 value should be 3402672, got {item1['value']}"
    
    item2 = result['items'][1]
    assert 'VALVE' in item2['description'], f"Item 2 should mention VALVE, got: {item2['description']}"
    assert item2['code'] == '3373119002', f"Item 2 code should be 3373119002, got {item2['code']}"
    assert item2['qty'] == 4, f"Item 2 qty should be 4, got {item2['qty']}"
    assert item2['value'] == Decimal('5200'), f"Item 2 value should be 5200, got {item2['value']}"
    
    item3 = result['items'][2]
    assert 'WHEEL BALANCE' in item3['description'], f"Item 3 should mention WHEEL BALANCE, got: {item3['description']}"
    assert item3['code'] == '21004', f"Item 3 code should be 21004, got {item3['code']}"
    assert item3['qty'] == 4, f"Item 3 qty should be 4, got {item3['qty']}"
    assert item3['unit'] == 'PCS', f"Item 3 unit should be PCS, got {item3['unit']}"
    assert item3['value'] == Decimal('50848'), f"Item 3 value should be 50848, got {item3['value']}"
    
    item4 = result['items'][3]
    assert 'WHEEL ALIGNMENT' in item4['description'], f"Item 4 should mention WHEEL ALIGNMENT, got: {item4['description']}"
    assert item4['code'] == '21019', f"Item 4 code should be 21019, got {item4['code']}"
    assert item4['qty'] == 1, f"Item 4 qty should be 1, got {item4['qty']}"
    assert item4['unit'] == 'UNT', f"Item 4 unit should be UNT, got {item4['unit']}"
    assert item4['value'] == Decimal('25424'), f"Item 4 value should be 25424, got {item4['value']}"
    
    print("\n✓ PASS: All line items extracted correctly")
    
    # Test 4: Additional Fields
    print("\n4. ADDITIONAL FIELDS")
    print("-" * 80)
    print(f"Payment Method: {result['payment_method']}")
    print(f"Delivery Terms: {result['delivery_terms']}")
    print(f"Remarks: {result['remarks']}")
    print(f"Attended By: {result['attended_by']}")
    print(f"Kind Attention: {result['kind_attention']}")
    
    assert result['payment_method'] == 'on_delivery', f"Payment method should be on_delivery, got {result['payment_method']}"
    assert result['delivery_terms'] == 'ex-stock', f"Delivery terms should be ex-stock, got {result['delivery_terms']}"
    assert 'conformed order' in result['remarks'].lower(), f"Remarks should contain 'conformed order'"
    assert result['attended_by'] == 'Sales Point', f"Attended by should be Sales Point, got {result['attended_by']}"
    assert result['kind_attention'] == 'Valued Customer', f"Kind Attention should be Valued Customer, got {result['kind_attention']}"
    
    print("✓ PASS: Additional fields extracted correctly")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)

if __name__ == '__main__':
    try:
        test_extraction()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
