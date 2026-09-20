# ฟังก์ชันที่เราต้องการทดสอบ (ปกติจะอยู่ในไฟล์ src)
def add(x, y):
    return x + y
# ฟังก์ชัน Test
def test_add_positive_numbers():
    result = add(2, 3) 
    assert result == 5 # ตรวจสอบว่า 2+3 ต้องเท่ากับ 5
def test_add_negative_numbers():
    result = add(-1, -1)
    assert result == -2