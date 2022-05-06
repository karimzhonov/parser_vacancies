import json
import os


def execute_macros(excel_path, style=None):
    cd = os.path.dirname(__file__)
    if style is None: style = json.load(open(os.path.join(cd, '../config.json'), encoding='utf-8'))['style']
    style1 = style.capitalize()
    style2 = f"20% — {style1.lower()}"
    code = f"""
Private Sub my_macros()
    Dim xlApp, Book, Sheet
    Set xlApp = CreateObject("Excel.Application")
    Set Book = xlApp.Workbooks.Open(WScript.Arguments(0))
    For Each Sheet In Book.Worksheets
        Sheet.Columns("A:G").EntireColumn.AutoFit
        Sheet.Columns("A:G").Style = "Вывод"
        Sheet.Columns("A:G").Style = "{style2}"
        Sheet.Range("A1:G1").Style = "{style1}"
    Next
    Book.Sheets(1).Activate
    Book.Save
    Book.Close True
    xlApp.Quit
End Sub

Call my_macros
    """
    filename = os.path.join(cd, 'macros.vbs')
    open(filename, 'w').write(code)
    os.system(f'{filename} {excel_path}')
    os.remove(filename)
