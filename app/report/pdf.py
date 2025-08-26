def xlsx_to_pdf_com(xlsx_path: str, pdf_path: str):
    """COM을 사용하여 Excel을 PDF로 내보내기"""
    import pythoncom
    from win32com.client import Dispatch
    
    pythoncom.CoInitialize()
    try:
        import os
        xl = Dispatch("Excel.Application")
        xl.Visible, xl.DisplayAlerts = False, False
        
        wb = xl.Workbooks.Open(os.path.abspath(xlsx_path))
        wb.ExportAsFixedFormat(0, os.path.abspath(pdf_path))  # 0=xlTypePDF
        wb.Close(SaveChanges=False)
        xl.Quit()
        
        print(f"✅ PDF 내보내기 완료: {pdf_path}")
        return True
        
    except Exception as e:
        print(f"❌ PDF 내보내기 실패: {e}")
        return False
        
    finally:
        pythoncom.CoUninitialize()

def xlsx_to_pdf_openpyxl(xlsx_path: str, pdf_path: str):
    """openpyxl을 사용한 PDF 내보내기 (제한적)"""
    try:
        # openpyxl로는 직접 PDF 변환이 불가능
        # 대신 HTML로 내보내기 후 브라우저에서 PDF 변환 안내
        print("⚠️ openpyxl로는 직접 PDF 변환이 불가능합니다.")
        print("대안:")
        print("1. COM 엔진 사용: --engine com")
        print("2. 브라우저에서 열기 후 PDF로 저장")
        print("3. 온라인 변환 도구 사용")
        return False
        
    except Exception as e:
        print(f"❌ PDF 내보내기 실패: {e}")
        return False
