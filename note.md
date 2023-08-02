https://a.4cdn.org/po/thread/570368.json
https://github.com/4chan/4chan-API/blob/master/pages/Threads.md
thread 內容包含 orignal post 以及 reply to it, textual information


`nohup python src/requester.py -b po`
`nohup` to prevent program terminating after terminal closing
This will generate a nohup.out

------------------------------------------------------------------------------------------------

三大區塊
處理要 update 的 board
下載 thread list per board
下載 thread content

中斷性的問題
每次重啟 threads_on_boards 就會被刷新，中間間隔的資料就會被跳過
但也有可能還是有某些post 存在在板上，所以可能會產生重複資料下載的問題

重複性的問題
要看一個版刷新多久 post 多久被刪一次
儲存的資料夾命名方式，來看會不會跨天數同post 都會被存下來 (這樣就變成 double copy)
然後同一天的同筆資料 如果會不會因為更新而更新同一個檔案，還是變成 double copy
又如果 scraper 中斷的話 以上問題會不會出現


Output is in data/saves/{today_date}/threads/{board_code}/{OP_ID}_{update_UTC_TIME}.json

4chan API
https://github.com/4chan/4chan-API/blob/master/pages/Endpoints_and_domains.md

This two are extracted
 Thread list
 Threads


Report:
    1. What happened when you start data collection code?
        including multi-thread idea
        - one board is one thread?
        - after collect the thread (post) list of a board
        - download all the thread (post) including the textual contents
        - constantly check if there is an update for a thread (post) or new thread (what index used to match updated thread to downloaded thread)
        - if there is an update thread, then update or download the thread (post)
        (need more detail)

    2. Downloaded thread format, each file is the original post (OP) and all the replies to it
        - Downloaded naming?

    3. How often does a thread (post) got deleted

Try: Scraping multiple boards to see if it works

Other tools: How to store it (MongoDB?), (Dbt?) how to transform it, how to create offer?

collect questions (for massimo because he is an expert)



flow

#_load_old_monitors
    1. _update_monitoring_boards determine the board to scrap in this round and stored them into self.monitoring_boards which is a list
    also set self._check_new_boards = False which is weird

    2. based on the board to scarp in this round, check if there are thread files saved in "today" if so, then pick them up to self.monitoring_threads[board][thread_id] = [last_modified, replies]

#While Loop

A. if self._check_new_boards, rerun _update_monitoring_boards (it will never be run unless we implement _update_monitoring_boards)

B. self._update_monitoring_threads()
    loop through the board that we decided to monitor
    1. get_and_save_single_board_threadlist()
        I. threadlist = self.get_single_board_threadlist(board_code)
        collect threadlist for each board
        self._last_requested[board_code]["board"] = time  # this is to keep track of the last request time for current board

        II. delete the previous saved threadlist for board, and save the new threadlist 
        self.threads_on_board[board][thread_id] = [last_modified, replies]

    2. if threads_id from self.monitoring_threads[board][thread_id] = [last_modified, replies] is not on self.threads_on_board, then the thread died, delete it from self._last_requested (but why not on monitoring_threads too?)
    if they are, meaning 
     then we check if their last_modified is updated, if so then recorded into self._posts_to_update.append([board, thread]), if not then its a new born one, also record to _posts_to_update

    then proccess the one on the board, if they are on the monitoring list, then check update, if update, then update the monitoring thread, if not on the monitoring list, then its new born, either new born or update will be recorded in self._posts_to_update
    (first check monitoring board, if they are not on thread on board meaning dead, then check thread on board with monitoring board, if they are on monitoring board, check update, if not they are new born)
    self._posts_to_update.append([board, thread])


C. self._update_posts_on_monitoring_threadlist()
    for board, post in self._posts_to_update:
    1. self.get_and_save_thread(board, post)
        
        iterate over today's saved thread's folder,
        check if the saved thread ID is equal to thread id we want to update
        if so, update the file (overwrite), else write another file (save regardlessly)

        I. get_thread(boardID, threadID)
            request thread content using thread API, retry 5 times,
            if its error outside of 200 success or 304 (no update content)
             wait self._request_time_limit * 5
            return r_thread.json()