from PIL import Image
import numpy as np

img = Image.open(r'C:\Users\username\Downloads\ChatGPT Image 2026년 5월 20일 오전 08_47_47.png')
arr = np.array(img)
cell = 229

print("=== 셀 경계선 픽셀 일관성 검증 ===")
for col in range(1, 6):
    x = col * cell
    col_pixels = arr[:, x, :]
    print(f"  열 경계 x={x}: 평균RGB=({col_pixels[:,0].mean():.0f}, {col_pixels[:,1].mean():.0f}, {col_pixels[:,2].mean():.0f})")

print()
for row in range(1, 5):
    y = row * cell
    row_pixels = arr[y, :, :]
    print(f"  행 경계 y={y}: 평균RGB=({row_pixels[:,0].mean():.0f}, {row_pixels[:,1].mean():.0f}, {row_pixels[:,2].mean():.0f})")

print()
print("=== 각 셀 중심 픽셀 밝기 (아이콘 존재 확인) ===")
for r in range(5):
    row_info = []
    for c in range(6):
        cx = c * cell + cell // 2
        cy = r * cell + cell // 2
        px = arr[cy, cx]
        brightness = int(px.mean())
        row_info.append(f"{brightness:3d}")
    sep = " | "
    print(f"  행{r+1}: {sep.join(row_info)}")
