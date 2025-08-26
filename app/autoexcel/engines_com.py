import pythoncom
from win32com.client import Dispatch

class ComExcel:
    def __enter__(self):
        try:
            pythoncom.CoInitialize()
            
            # 새 Excel 인스턴스 생성 (더 안전함)
            self.app = Dispatch("Excel.Application")
            print("[debug] 새 Excel 인스턴스 생성 성공")
            
        except Exception as e:
            print(f"[debug] Excel COM 객체 생성 실패: {e}")
            raise
        
        # 속성 설정은 선택사항으로 처리
        try:
            self.app.Visible = False
            print("[debug] Excel Visible = False 설정 성공")
        except:
            print("[debug] Excel Visible 속성 설정 건너뜀")
        
        try:
            self.app.DisplayAlerts = False  # False로 변경하여 경고 억제
            print("[debug] Excel DisplayAlerts = False 설정 성공")
        except:
            print("[debug] Excel DisplayAlerts 속성 설정 건너뜀")
        
        return self
    def __exit__(self, exc_type, exc, tb):
        try: self.app.Quit()
        finally: pythoncom.CoUninitialize()

    def open(self, path):
        try:
            print(f"[debug] Excel에서 파일 열기 시도: {path}")
            wb = self.app.Workbooks.Open(path)
            print(f"[debug] 파일 열기 성공: {wb.Name}")
            return wb
        except Exception as e:
            print(f"[debug] 파일 열기 실패: {e}")
            print(f"[debug] 새 워크북 생성")
            wb = self.app.Workbooks.Add()
            return wb

def create_pivot_chart(path_in, path_out, src_sheet, tgt_sheet, rows, values, chart_type="bar"):
    # 절대 경로로 변환
    import os
    abs_path_in = os.path.abspath(path_in)
    abs_path_out = os.path.abspath(path_out)
    
    print(f"[debug] 입력 파일 절대 경로: {abs_path_in}")
    print(f"[debug] 출력 파일 절대 경로: {abs_path_out}")
    
    # 파일 존재 확인
    if not os.path.exists(abs_path_in):
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {abs_path_in}")
    
    with ComExcel() as cx:
        wb = cx.open(abs_path_in)
        # 시트 이름이 없으면 첫 번째 시트 사용
        if src_sheet:
            try:
                ws = wb.Worksheets(src_sheet)
            except:
                ws = wb.Worksheets(1)  # 첫 번째 시트 사용
        else:
            ws = wb.Worksheets(1)
        
        print(f"[debug] 워크시트 '{ws.Name}' 선택됨")
        print(f"[debug] 워크북 경로: {wb.FullName}")
        print(f"[debug] 시트 수: {wb.Worksheets.Count}")
        
        # 셀 값 직접 확인
        print(f"[debug] A1 값: '{ws.Range('A1').Value}'")
        print(f"[debug] A2 값: '{ws.Range('A2').Value}'")
        print(f"[debug] B1 값: '{ws.Range('B1').Value}'")
        print(f"[debug] B2 값: '{ws.Range('B2').Value}'")
            
        # 데이터 범위 추정 - 더 안전한 방법 사용
        try:
            # 먼저 CurrentRegion 시도
            src_rng = ws.Range("A1").CurrentRegion
            print(f"[debug] CurrentRegion: {src_rng.Rows.Count}행 x {src_rng.Columns.Count}열")
            if src_rng.Rows.Count < 2:
                raise ValueError("CurrentRegion이 2행 미만")
        except Exception as e:
            print(f"[debug] CurrentRegion 실패: {e}")
            # CurrentRegion 실패 시 수동으로 범위 계산
            last_row = ws.Cells(ws.Rows.Count, 1).End(-4162).Row  # xlUp
            last_col = ws.Cells(1, ws.Columns.Count).End(-4159).Column  # xlToLeft
            
            print(f"[debug] 수동 계산: last_row={last_row}, last_col={last_col}")
            
            if last_row < 2:
                # 더 강력한 방법 시도: UsedRange 사용
                used_range = ws.UsedRange
                print(f"[debug] UsedRange: {used_range.Rows.Count}행 x {used_range.Columns.Count}열")
                if used_range.Rows.Count >= 2:
                    src_rng = used_range
                else:
                    raise ValueError("피벗 테이블을 만들려면 최소 2행의 데이터가 필요합니다")
            else:
                # 실제 데이터가 있는 범위로 설정
                src_rng = ws.Range(f"A1:{chr(64 + last_col)}{last_row}")
                print(f"[debug] 수동 범위 설정: A1:{chr(64 + last_col)}{last_row} (행: {last_row}, 열: {last_col})")
        # Pivot
        pcache = wb.PivotCaches().Create(1, src_rng)  # 1:xlDatabase
        tgt = None
        for s in wb.Sheets:
            if s.Name == tgt_sheet: tgt = s
        if tgt is None: tgt = wb.Worksheets.Add(); tgt.Name = tgt_sheet
        pvt = pcache.CreatePivotTable(TableDestination=f"{tgt_sheet}!R3C1", TableName="피벗테이블1")
        # 필드 배치
        for r in rows:
            try: 
                tgt.PivotTables("피벗테이블1").PivotFields(r).Orientation = 1  # xlRowField
                print(f"[debug] 행 필드 추가: {r}")
            except Exception as e: 
                print(f"[debug] 행 필드 {r} 추가 실패: {e}")
                pass
        
        for col, agg in values:
            try:
                pf = tgt.PivotTables("피벗테이블1").PivotFields(col)
                tgt.PivotTables("피벗테이블1").AddDataField(pf, f"Sum of {col}", -4157)  # -4157=xlSum
                print(f"[debug] 값 필드 추가: {col} ({agg})")
            except Exception as e:
                print(f"[debug] 값 필드 {col} 추가 실패: {e}")
                pass
        
        # 차트
        try:
            # 피벗 테이블이 있는 시트를 명시적으로 선택
            pvt_sheet = wb.Worksheets(tgt_sheet)
            pvt_sheet.Activate()
            
            # 피벗 테이블의 데이터 범위 가져오기
            pivot_table = pvt_sheet.PivotTables("피벗테이블1")
            
            # 차트 생성
            ch = wb.Charts.Add()
            ch.ChartType = 51 if chart_type=="bar" else 4  # 51=xlColumnClustered, 4=xlLine
            
            # 피벗 테이블의 데이터 범위를 차트 소스로 사용
            chart_data_range = pivot_table.TableRange1
            print(f"[debug] 차트 데이터 범위: {chart_data_range.Address}")
            
            ch.SetSourceData(chart_data_range)
            
            # 차트 제목 설정
            if hasattr(ch, 'ChartTitle'):
                ch.ChartTitle.Text = f"{chart_type.title()} 차트"
            
            print(f"[debug] 차트 생성 완료: {ch.Name}")
            
        except Exception as e:
            print(f"[debug] 차트 생성 중 오류: {e}")
            # 차트 생성 실패 시에도 계속 진행
            pass
        
        # Excel 종료 보장
        try:
            wb.SaveAs(path_out)
        finally:
            wb.Close(SaveChanges=1)
