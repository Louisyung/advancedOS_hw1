# 開始寫之前，先回答自己四個問題。這四個也是報告裡要寫的設計決策：

# 1. reference bit 什麼時候設成 1？
#    → 每次存取（hit 或剛載入）都設成 1。dirty bit 則和 FIFO、MFU 一樣，只有寫入時才設成 1。
# 2. 四種類別的優先順序？用 (reference, dirty) 表示，越前面越優先被換出：
#    (0,0) 最近沒用、沒改過 → 最好的受害頁，換出不用寫回
#    (0,1) 最近沒用、有改過 → 換出要寫回磁碟
#    (1,0) 最近有用、沒改過 → 可能很快又會用到
#    (1,1) 最近有用、有改過 → 最不該換出
#    → 也就是說：寧可換出一頁「最近有用但乾淨」的，也不要換出「最近沒用但很髒」的嗎？想一想為什麼課本把 (0,1) 排在 (1,0) 前面。
# 3. 掃描的規則？（課本的版本，建議照這個做，結果才對得上下面的數字）
#    → 第一輪：從指針開始繞一圈，找 (0,0)，「不改任何 bit」。找到就換它。
#    → 第二輪：再繞一圈，找 (0,1)，沿路「把經過的頁的 reference bit 清成 0」。找到就換它。
#    → 兩輪都沒找到：這時所有 reference bit 都已經是 0 了，回到第一輪再找一次，一定找得到。
# 4. 中斷要不要多算？清 reference bit 是在處理 page fault 的過程中順便做的，已經在同一次中斷裡，
#    所以不另外算。規則和 FIFO 一樣：fault 一次 +1，換出的頁是 dirty 要寫回，再 +1。

# 第二層：資料結構和流程

# 這次「順序」又重要了（像 FIFO），而且指針要繞圈，所以要記錄：
# - frames：一個 list，代表記憶體裡的 frame，frames[i] 是第 i 個 frame 放的頁號。
#   這次不用 deque，因為換出的頁不一定在最前面，新頁要「放回 victim 原本的位置」(frames[i] = page)，
#   這樣循環的順序才不會亂。
# - ref：dict，頁號 → reference bit，同時用來判斷頁是否在記憶體中（就像 MFU 的 count）。
# - dirty：dict，頁號 → dirty bit。
# - hand：整數，時鐘指針，指向下一次要從哪個 frame 開始掃。往前走用 hand = (hand + 1) % n_frames 繞回 0。

# 每次存取的流程：
# - hit：reference bit 設成 1。
# - fault：fault 和中斷各加 1
#   → 記憶體沒滿：新頁直接 append 到 frames 尾端，指針不動。
#   → 記憶體滿了：用上面的規則找出受害頁的「位置」i → dirty 就寫回 → 刪掉它在 ref、dirty 的紀錄
#     → frames[i] = 新頁 → 指針移到 i 的下一格。
#   → 新頁：ref = 1、dirty = False。
#   （MFU 學到的教訓：「載入新頁」不管記憶體滿不滿都一樣，只寫一份。）
# - 最後，如果是寫入，就把 dirty 設成 True，和 FIFO 一樣。

# 函式的參數和回傳值都要和 fifo()、mfu() 一樣，(refs, n_frames) → (faults, interrupts, disk_writes)。

# 第三層：找受害頁的寫法

# 建議寫一個 while True 迴圈包住「第一輪 + 第二輪」，每一輪是 for _ in range(n_frames) 繞一圈：
# - 每看一格：檢查 frames[hand] 這頁的 (ref, dirty) 是不是你要找的。
#   是 → 記下位置、跳出；不是 → （第二輪才要清 reference bit）→ hand 往前一格。
# - 注意：找到的時候 hand 還停在 victim 那一格，「放新頁、指針移到下一格」要在找到之後才做。
# - 想想看：第二輪清 reference bit 時，要不要清「被選中的那一頁」？（它都要被換出了，清不清有差嗎？）
# - 想想看：最多會繞幾圈？為什麼 while True 一定會結束？

# 寫完用這些結果檢查

# 小測資（S = lambda l: [(p, False) for p in l]）：

# ┌──────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────┐
# │                           測試                           │                         預期結果                         │
# ├──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
# │ esc(S([1,2,3,4]), 3)                                     │ (4, 4, 0)：全部 (1,0)，第二輪清完 bit 後換掉頁 1         │
# ├──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
# │ esc(S([1,2,3,4,2,5,2]), 3)                               │ (5, 5, 0)：頁 2 被 hit 過有第二次機會，最後一次還在記憶體 │
# │                                                          │ （FIFO 會是 (6, 6, 0)）                                  │
# ├──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
# │ esc([(1,True),(2,False),(3,False),(4,False),(1,False)], 3) │ (4, 4, 0)：頁 1 是 dirty，優先換掉乾淨的頁 2，所以最後  │
# │                                                          │ 存取頁 1 是 hit（FIFO 會是 (5, 6, 1)）                   │
# ├──────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
# │ esc([(1,True),(2,True),(3,False)], 2)                    │ (3, 4, 1)：全部都是 dirty，只能換出 (0,1) 並寫回         │
# └──────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────┘

# 如果你照上面的規則做，main.py 跑出來的應該是：

# ┌──────────┬─────────────────────────┬─────────────────────────┐
# │ 參考字串 │        10 frames        │       100 frames        │
# ├──────────┼─────────────────────────┼─────────────────────────┤
# │ Random   │ (148971, 193849, 44878) │ (139777, 183266, 43489) │
# ├──────────┼─────────────────────────┼─────────────────────────┤
# │ Locality │ (108005, 147000, 38995) │ (5303, 10162, 4859)     │
# ├──────────┼─────────────────────────┼─────────────────────────┤
# │ Matrix   │ (50171, 50260, 89)      │ (49787, 49876, 89)      │
# └──────────┴─────────────────────────┴─────────────────────────┘

# 可以跟 MFU 比一下 Matrix 那一列：disk writes 從兩萬多掉到 89，為什麼？（提示：Matrix 裡哪些頁會被寫入？
# ESC 會不會把它們換出去？）這很適合寫進報告的討論。

# 數字對不上的話，先看小測資哪一個錯了：
# - 第 1 個錯 → 第二輪清 reference bit 或指針的處理有問題
# - 第 2 個錯 → hit 沒設 reference bit，或指針沒有從上次的位置繼續
# - 第 3 個錯 → 類別的優先順序或第一輪的條件有問題
# - 第 4 個錯 → dirty 寫回或中斷的計算有問題
# 寫好或卡住的時候，把程式貼給我看。


# frames[i] = [頁號, ref, dirty]，i 就是第 i 號 frame
def esc(refs,n_frames):
    frame_id = []               # maintain記憶體中每個frame放的頁號（frame_id[i] = 第i個frame的頁號）
    refer = []                  # maintain記憶體中frame對應的reference
    dirty = []                  # maintain記憶體中frame對應的dirty bit
    position = {}               # 紀錄frame中放哪些page頁號
    pointer = 0                 # 決定下一個要檢查的指標
    faults = 0 
    interrupts = 0
    disk_writes = 0
    for page, is_write in refs:
        is_find = 0
        if page in position:            # page hit
            refer[position[page]] = 1
            if is_write:
                dirty[position[page]] = is_write
        else:                                   # page fault
            faults += 1
            interrupts += 1
            if len(position)==n_frames:         # 需進行replacement
                while(not is_find):
                    for i in range (n_frames):      # 找refer跟dirty為0,0
                        index = (i+pointer) % n_frames
                        if not refer[index]:
                            if not dirty[index]:        # 代表此為replace的victim頁
                                victim = index
                                is_find = 1
                                break
                    if not is_find:
                        for i in range(n_frames):       # 找refer跟dirty為0,1
                            index = (i+pointer) % n_frames
                            if not refer[index]:
                                if dirty[index]:            # 找到(0,1)，作為victim
                                    victim = index
                                    is_find = 1
                                    break
                            else:
                                refer[index] = 0            # 沒被選中，清掉reference bit，給它最後一次機會
                if dirty[victim]:
                    disk_writes += 1
                    interrupts += 1
                del(position[frame_id[victim]]) # 先用位置查出舊頁號，刪掉舊頁的紀錄
                frame_id[victim] = page
                refer[victim] = 1
                dirty[victim] = is_write
                position[page] = victim         # 新頁的頁號 → 所在位置
                pointer = (victim+1) % n_frames # 指針移到victim的下一格，%避免超出n_frames的size
            else:                               # 有空的frame可以直接放page
                position[page] = len(frame_id)  # append之前的長度就是新頁的位置
                frame_id.append(page)
                refer.append(1)
                dirty.append(is_write)          # 記憶體沒滿時指針不動
    return faults, interrupts, disk_writes