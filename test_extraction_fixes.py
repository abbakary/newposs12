#!/usr/bin/env python
"""
Test script to validate invoice extraction fixes for Superdoll invoices
Tests address, phone, and line item description extraction
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tracker.utils.pdf_text_extractor import parse_invoice_data

# Test invoice text (simulating OCR output from Superdoll invoice T 964 DNA)
test_invoice_text = """Superdoll Trailer Manufacture Co. (T) Ltd.
P.O. Box 16541 DSM, Tel.+255-22-2860930-2863467, Fax +255-22-2865412/3, Email: stm@superdoll-tz.com,Tax ID No.100-199-157, VAT Reg. No.10-0085-15-E

Proforma Invoice

Code No : A01218
Customer Name : SAID SALIM BAKHRESA CO LTD
Address
P.O.BOX 2517
DAR-ES-SALAAM
TANZANIA

Tel : 2180007/2861940
Fax :
Del. Date : 27/10/2025
PI No. : PI-1765684
Date : 27/10/2025
Cust Ref :
Ref Date :
Attended By : Sales Point
Kind Attention : Valued Customer
Reference : FOR T 964 DNA

Sr No. Item Code Description Type Qty Rate TSH Value TSH
1 41003 STEERING AXLE ALIGNMENT 1 NOS 100,000.00 100,000.00

Net Value : TSH 100,000.00
VAT : TSH 18,000.00
Gross Value : TSH 118,000.00

Payment : Cash/Chq on Delivery
Delivery : ex-stock
Remarks : Looking forward to your conformed order

NOTE 1 : Payment in TSHS accepted at the prevailing rate on the date of payment.
2 : Proforma Invoice is Valid for 2 weeks from date of Proforma.
3 : Discount is Valid only for the above Quantity.
4 : Duty and VAT exemption documents to be submitted with the Purchase Order.
"""

def test_extraction():
    """Test the extraction and print results"""
    print("=" * 80)
    print("TESTING INVOICE EXTRACTION FIXES")
    print("=" * 80)
    
    result = parse_invoice_data(test_invoice_text)
    
    # Test 1: Customer Name
    print("\n1. CUSTOMER NAME EXTRACTION")
    print("-" * 80)
    expected_customer = "SAID SALIM BAKHRESA CO LTD"
    actual_customer = result.get('customer_name', '')
    
    print(f"Expected: {expected_customer}")
    print(f"Actual:   {actual_customer}")
    
    if actual_customer == expected_customer:
        print("✓ PASS: Customer name extracted correctly")
    else:
        print("✗ FAIL: Customer name mismatch")
        # Check if it at least has the main name without extra labels
        if "SAID SALIM BAKHRESA" in actual_customer:
            print("  (Contains correct name, but may have extra content)")
    
    # Test 2: Address
    print("\n2. ADDRESS EXTRACTION")
    print("-" * 80)
    actual_address = result.get('address', '')
    
    print(f"Actual: {actual_address}")
    
    # Check if address contains expected components
    has_pob = "P.O.BOX" in actual_address or "P.O BOX" in actual_address
    has_dar = "DAR" in actual_address
    has_tanzania = "TANZANIA" in actual_address
    
    print(f"  Has P.O.BOX: {has_pob}")
    print(f"  Has DAR-ES-SALAAM: {has_dar}")
    print(f"  Has TANZANIA: {has_tanzania}")
    
    if has_pob and has_dar and has_tanzania:
        print("✓ PASS: Address contains all expected components")
    elif has_pob or has_dar or has_tanzania:
        print("⚠ PARTIAL: Address has some correct components but missing some")
    else:
        print(f"✗ FAIL: Address extraction failed or incomplete")
        print(f"  Expected to contain: P.O.BOX 2517, DAR-ES-SALAAM, TANZANIA")
    
    # Test 3: Phone
    print("\n3. PHONE EXTRACTION")
    print("-" * 80)
    expected_phone = "2180007/2861940"
    actual_phone = result.get('phone', '')
    
    print(f"Expected: {expected_phone}")
    print(f"Actual:   {actual_phone}")
    
    # Normalize for comparison (might have spaces)
    actual_normalized = actual_phone.replace(' ', '').replace('-', '/')
    expected_normalized = expected_phone.replace(' ', '').replace('-', '/')
    
    if actual_normalized == expected_normalized or actual_phone.startswith("2180007"):
        print("✓ PASS: Phone number extracted correctly")
    elif actual_phone:
        print("⚠ PARTIAL: Phone extracted but may not be exactly correct")
    else:
        print(f"✗ FAIL: Phone extraction failed")
        print(f"  Should NOT contain: Tel, Fax, Date, PI, etc.")
    
    # Test 4: Line Item Description
    print("\n4. LINE ITEM DESCRIPTION EXTRACTION")
    print("-" * 80)
    items = result.get('items', [])
    
    print(f"Number of items found: {len(items)}")
    
    if items:
        for idx, item in enumerate(items, 1):
            desc = item.get('description', '')
            qty = item.get('qty', 0)
            value = item.get('value', 0)
            
            print(f"\nItem {idx}:")
            print(f"  Description: {desc}")
            print(f"  Qty: {qty}")
            print(f"  Value: {value}")
            
            if "STEERING AXLE" in desc or "STEERING" in desc.upper():
                print("  ✓ PASS: Description contains expected product name")
            elif desc:
                print("  ⚠ PARTIAL: Description found but may be incomplete")
            else:
                print("  ✗ FAIL: Description is empty")
    else:
        print("✗ FAIL: No items extracted")
    
    # Test 5: Monetary Values
    print("\n5. MONETARY VALUES EXTRACTION")
    print("-" * 80)
    subtotal = result.get('subtotal')
    tax = result.get('tax')
    total = result.get('total')
    
    print(f"Subtotal: {subtotal} (expected: 100000.00)")
    print(f"Tax:      {tax} (expected: 18000.00)")
    print(f"Total:    {total} (expected: 118000.00)")
    
    tests_passed = 0
    if subtotal and float(subtotal) == 100000.00:
        print("  ✓ Subtotal correct")
        tests_passed += 1
    else:
        print("  ✗ Subtotal incorrect")
    
    if tax and float(tax) == 18000.00:
        print("  ✓ Tax correct")
        tests_passed += 1
    else:
        print("  ✗ Tax incorrect")
    
    if total and float(total) == 118000.00:
        print("  ✓ Total correct")
        tests_passed += 1
    else:
        print("  ✗ Total incorrect")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nKey fields to verify:")
    print(f"  ✓ Customer Name: {'PASS' if result.get('customer_name') == expected_customer else 'NEEDS REVIEW'}")
    print(f"  ✓ Address: {'PASS' if has_pob and has_dar and has_tanzania else 'NEEDS REVIEW'}")
    print(f"  ✓ Phone: {'PASS' if actual_phone and not any(x in actual_phone.upper() for x in ['TEL', 'FAX', 'DATE', 'PI']) else 'NEEDS REVIEW'}")
    print(f"  ✓ Description: {'PASS' if items and items[0].get('description') else 'NEEDS REVIEW'}")
    print(f"  ✓ Monetary Values: {'PASS' if tests_passed == 3 else f'{tests_passed}/3 CORRECT'}")

if __name__ == '__main__':
    test_extraction()
