from collections import deque

def fifo(refs, n_frames):
    """FIFO 分頁置換演算法：記憶體滿了就換出最早載入的頁
    refs：參考字串 [(頁號, 是否寫入), ...]
    n_frames：主記憶體的 frame 數量
    回傳 (page fault 次數, 中斷次數, 寫回磁碟的頁數)"""
    queue = deque()       # 記憶體中的頁，依載入順序排列，最左邊是最早載入的
    dirty = {}            # 記憶體中的頁 → dirty bit，同時用來判斷頁是否在記憶體中
    faults = 0            # page fault 次數
    interrupts = 0        # 中斷次數
    disk_writes = 0       # 寫回磁碟的頁數

    for page, is_write in refs:
        if page not in dirty:                  # 頁不在記憶體中：page fault
            faults += 1
            interrupts += 1                    # page fault 要 trap 進 OS 處理，算一次中斷

            if len(queue) == n_frames:         # 記憶體已滿，換出最早載入的頁
                victim = queue.popleft()
                if dirty.pop(victim):          # 被換出的頁被修改過，要先寫回磁碟
                    disk_writes += 1
                    interrupts += 1            # 寫回磁碟需要 OS 發出 I/O，再算一次中斷

            queue.append(page)                 # 新頁放到佇列尾端
            dirty[page] = False                # 剛從磁碟載入，內容和磁碟一致

        if is_write:                           # 寫入：設定 dirty bit
            dirty[page] = True

    return faults, interrupts, disk_writes