import random


PAGE_MIN = 1          # 最小頁號
PAGE_MAX = 1500       # 最大頁號
N_REFS = 150000       # 記憶體存取次數
WRITE_PROB = 0.3      # 每次存取是「寫入」的機率


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


if __name__ == "__main__":
    random.seed(555)  

    random_refs = generate_random(N_REFS, WRITE_PROB)
    locality_refs = generate_locality(N_REFS, WRITE_PROB)

    print_stats("Random", random_refs)
    print_stats("Locality", locality_refs)