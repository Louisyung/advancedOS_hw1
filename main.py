import math
import random
import FIFO

PAGE_MIN = 1          # 最小頁號
PAGE_MAX = 1500       # 最大頁號
N_REFS = 150000       # 記憶體存取次數
WRITE_PROB = 0.3      # 每次存取是「寫入」的機率
FRAMES = range(10, 101, 10)   # 要測試的 frame 數量：10, 20, ..., 100

# 自訂參考字串：神經網路全連接層 C = A × B
# A: 50 x 600 , B: 600 x 35 , C: 50 x 35
N_SAMPLES = 50        # 輸入資料筆數（A、C 的列數）
N_FEATURES = 600      # 每筆資料的特徵數（A 的行數 = B 的列數）
N_OUTPUTS = 35        # 每筆資料的輸出數（B、C 的行數）
ELEMS_PER_PAGE = 36   # 一頁可放 36 個元素，每一列都從新的一頁開始存放
SPARSITY = 0.1        # 特徵值為 0 的機率，為 0 時乘積必為 0，可跳過不算

A_ROW_PAGES = math.ceil(N_FEATURES / ELEMS_PER_PAGE)   # A 一列佔 17 頁
B_ROW_PAGES = math.ceil(N_OUTPUTS / ELEMS_PER_PAGE)    # B 一列佔 1 頁
C_ROW_PAGES = B_ROW_PAGES                              # C 一列和 B 一列一樣是 35 個元素

A_START = PAGE_MIN                                     # A：頁號 1 ~ 850
B_START = A_START + N_SAMPLES * A_ROW_PAGES            # B：頁號 851 ~ 1450
C_START = B_START + N_FEATURES * B_ROW_PAGES           # C：頁號 1451 ~ 1500


def generate_random(n, write_prob):
    """產生 Random 參考字串，回傳 [(頁號, 是否寫入), ...]"""
    refs = []
    for _ in range(n):
        page = random.randint(PAGE_MIN, PAGE_MAX)       # 1~1500 隨機挑一個
        is_write = random.random() < write_prob         # 有 write_prob 的機率是 True
        refs.append((page, is_write))
    return refs


def generate_locality(n, write_prob):
    """產生 Locality 參考字串，模擬 procedure call"""
    refs = []
    while len(refs) < n:
        seg_len = random.randint(n // 200, n // 100)    # 這次 call 的長度：總長的 1/200 ~ 1/100
        base = random.randint(PAGE_MIN, PAGE_MAX)       # 這次 call 的起始頁
        ws_size = random.randint(20, 60)                # 這次 call 會用到幾頁（工作集大小）

        for _ in range(seg_len):
            offset = random.randrange(ws_size)                      # 0 ~ ws_size-1
            page = (base - 1 + offset) % PAGE_MAX + 1               # 超過 1500 就繞回 1
            is_write = random.random() < write_prob
            refs.append((page, is_write))

    return refs[:n]   # 最後一段可能讓總長度超過 n，截掉多出來的部分

def generate_matrix(n):
    """自訂參考字串：模擬神經網路全連接層 C = A × B（i-k-j 迴圈順序）
    A (50×600) 為輸入資料、B (600×35) 為所有資料共用的權重、C (50×35) 為輸出
    只做推論（forward），權重固定不更新，因此 A、B 只讀不寫，C 會被寫入
    50 筆算完後再對同一份資料重做推論，直到湊滿 n 次存取
    回傳 [(頁號, 是否寫入), ...]"""
    refs = []
    i = 0                                                  # 目前處理到第幾筆資料（跨輪次累計）
    while len(refs) < n:
        row = i % N_SAMPLES                                # 50 筆算完後，再對同一份資料重做一次推論（權重固定，B 不寫入）
        a_row_start = A_START + row * A_ROW_PAGES          # A 第 row 列的第一頁
        c_row_start = C_START + row * C_ROW_PAGES          # C 第 row 列的第一頁

        for k in range(N_FEATURES):                        # k 走過 B 的每一列
            # 讀 A[row][k]：第 k 個特徵落在 A 這一列的第 k // 36 頁
            a_page = a_row_start + k // ELEMS_PER_PAGE
            refs.append((a_page, False))

            # 特徵值為 0：A[row][k] × B[k][j] 必為 0，不必讀 B 也不必更新 C
            if random.random() < SPARSITY:
                continue

            # 內層 j 迴圈：C[row][j] += A[row][k] × B[k][j]，讀 B 第 k 列、寫 C 第 row 列
            for j in range(B_ROW_PAGES):
                refs.append((B_START + k * B_ROW_PAGES + j, False))
                refs.append((c_row_start + j, True))

        i += 1                                             # 換下一筆資料

    return refs[:n]


def print_stats(name, refs):
    """印出參考字串的基本統計，用來檢查產生器是否正確"""
    pages = [p for p, w in refs]
    writes = [w for p, w in refs]

    print(f"=== {name} ===")
    print("長度:", len(refs))
    print("頁號範圍:", min(pages), "~", max(pages))
    print("寫入比例:", sum(writes) / len(writes))
    print("前1000筆不同頁數:", len(set(pages[:1000])))
    print()


def print_results(algo_name, ref_name, algo, refs):
    """用 algo 跑過每一種 frame 數量，印出 page fault、中斷、寫回磁碟的次數"""
    print(f"=== {algo_name} / {ref_name} ===")
    print(f"{'frames':>6} {'faults':>8} {'interrupts':>10} {'disk writes':>11}")
    for n_frames in FRAMES:
        faults, interrupts, disk_writes = algo(refs, n_frames)
        print(f"{n_frames:>6} {faults:>8} {interrupts:>10} {disk_writes:>11}")
    print()


if __name__ == "__main__":
    random.seed(555)

    random_refs = generate_random(N_REFS, WRITE_PROB)
    locality_refs = generate_locality(N_REFS, WRITE_PROB)
    matrix_refs = generate_matrix(N_REFS)

    # print_stats("Random", random_refs)
    # print_stats("Locality", locality_refs)
    # print_stats("Matrix", matrix_refs)

    print_results("FIFO", "Random", FIFO.fifo, random_refs)
    print_results("FIFO", "Locality", FIFO.fifo, locality_refs)
    print_results("FIFO", "Matrix", FIFO.fifo, matrix_refs)