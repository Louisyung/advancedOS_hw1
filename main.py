import random

# ===== 全域設定 =====
PAGE_MIN = 1          
PAGE_MAX = 1500       
N_REFS = 150000       
WRITE_PROB = 0.3      


def generate_random(n, write_prob):
    """產生 Random 參考字串，回傳 [(頁號, 是否寫入), ...]"""
    refs = []
    for _ in range(n):
        page = random.randint(PAGE_MIN, PAGE_MAX)       
        is_write = random.random() < write_prob       
        refs.append((page, is_write))
    return refs


def generate_locality(n, write_prob):
    """產生 Locality 參考字串，模擬 procedure call"""
    refs = []
    while len(refs) < n:
        seg_len = random.randint(n // 200, n // 100)    
        base = random.randint(PAGE_MIN, PAGE_MAX)       
        ws_size = random.randint(20, 60)                

        for _ in range(seg_len):
            offset = random.randrange(ws_size)                      
            page = (base - 1 + offset) % PAGE_MAX + 1               
            is_write = random.random() < write_prob
            refs.append((page, is_write))

    return refs[:n]   


if __name__ == "__main__":
    random.seed(555)   

    # ----- Random 自我檢查 -----
    refs = generate_random(N_REFS, WRITE_PROB)
    pages = [p for p, w in refs]
    writes = [w for p, w in refs]

    print("=== Random ===")
    print("長度:", len(refs))
    print("頁號範圍:", min(pages), "~", max(pages))
    print("寫入比例:", sum(writes) / len(writes))

    # ----- Locality 自我檢查 -----
    loc = generate_locality(N_REFS, WRITE_PROB)
    loc_pages = [p for p, w in loc]
    loc_writes = [w for p, w in loc]

    print("\n=== Locality ===")
    print("長度:", len(loc))
    print("頁號範圍:", min(loc_pages), "~", max(loc_pages))
    print("寫入比例:", sum(loc_writes) / len(loc_writes))

    # ----- 比較兩者的區域性 -----
    print("\n=== 前 1000 筆存取中，不同頁的數量 ===")
    print("Random  :", len(set(pages[:1000])))
    print("Locality:", len(set(loc_pages[:1000])))