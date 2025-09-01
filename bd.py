import psycopg2


def connect():
    conn = psycopg2.connect(database="eng-bot", user="postgres", password="postgres")
    return conn


def del_word(uid, word):
    conn = connect()
    with conn.cursor() as cur:
        sql = f"""
            select w.word_id, t.translate_id, ut.user_id 
            from words w, translates t, users_translates ut 
            where ut.user_id = {uid} 
                and ut.translate_id = t.translate_id
                and w.word_id = t.word_id
                and w.ru = '{word}';
            """
        cur.execute(sql)
        fa = cur.fetchall()
        if cur.rowcount == 0:
            sql = f"""select word_id from words where ru = '{word}' """
            cur.execute(sql)
            fa = cur.fetchone()

            sql = f"""
                insert into deleted (user_id, word_id) values ({uid}, {fa[0]});
            """
            cur.execute(sql)
            conn.commit()
            return

        sql = f"""
            delete from users_translates where user_id = {fa[len(fa)-1][2]} and translate_id = {fa[len(fa)-1][1]};
            """
        cur.execute(sql)
        if cur.rowcount == 0:
            conn.rollback()
            return
        sql = f"""
            delete from translates where translate_id = {fa[len(fa)-1][1]} and word_id = {fa[len(fa)-1][0]};
            """
        cur.execute(sql)
        if cur.rowcount == 0:
            conn.commit()
            return
        conn.commit()

        sql = f"""
            delete from words where word_id = {fa[len(fa)-1][0]} and ru = '{word}';
            """
        cur.execute(sql)
        if cur.rowcount == 0:
            conn.commit()
            return
        conn.commit()


def count(uid):
    conn = connect()
    with conn.cursor() as cur:
        sql = f"""
            select * from words w, translates t, users_translates ut
            where ut.user_id = '{uid}'
                and ut.translate_id = t.translate_id
                and t.word_id = w.word_id
            """
        cur.execute(sql)
        self = cur.rowcount
        sql = f"""
            select * from words w, translates t, users_translates ut
            where ut.user_id = '0'
                and ut.translate_id = t.translate_id
                and t.word_id = w.word_id
            """
        cur.execute(sql)
        base = cur.rowcount
        sql = f"""
            select * from deleted
            where user_id = '{uid}'
            """
        cur.execute(sql)
        deleted = cur.rowcount
        return (self, base, deleted, self + base - deleted)


def reset(uid):
    conn = connect()
    sql = f"""
        delete from deleted where user_id = '{uid}'
        """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def add_word(uid, word, en):
    conn = connect()
    if not en:  # Если вызов без перевода
        # есть ли слово в базовых
        sql = f"""
            select t.word_id wid, ru, en, ut.user_id uid, ut.translate_id tid
            from users_translates ut, translates t, words w
            where ut.translate_id = t.translate_id 
                and t.word_id = w.word_id 
                and ut.user_id = 0 
                and w.ru = '{word}'
            order by ru, t.translate_id DESC;
            """
        with conn.cursor() as cur:
            cur.execute(sql)
            rowcount = cur.rowcount
            fa = cur.fetchone()
        # есть слово в базовых
        if rowcount:
            # проверим, удалено ли оно
            word_id = fa[0]
            sql = f"""
                select * from deleted as d, words as w
                where d.user_id = {uid} and w.word_id = {word_id}  and d.word_id = w.word_id;
            """
            with conn.cursor() as cur:
                cur.execute(sql)
                rowcount = cur.rowcount
                fa = cur.fetchone()
            # не удалено
            if rowcount == 0:
                return (1, None)  # вернем ошибку
            # удалено, восстановим
            sql = f"""
                delete from deleted
                where user_id = {uid} and word_id = {word_id};
            """
            with conn.cursor() as cur:
                cur.execute(sql)
                rowcount = cur.rowcount
            # проверим как восстановилось
            if rowcount:
                conn.commit()
                sql = f"""
                    select * from deleted as d, words as w
                    where d.user_id = {uid} and w.word_id = {word_id}  and d.word_id = w.word_id;
                """
                with conn.cursor() as cur:
                    cur.execute(sql)
                    rowcount = cur.rowcount
                    fa = cur.fetchone()
                    # не восстановилось, вернем ошибку
                if rowcount:
                    return (3, None)
                # восстановилось, успех
                return (2, None)
            else:
                # не восстановилось, вернем ошибку
                return (3, None)

        # нет слова в базовых
        # проверяем наличие перевода в базе пользователя
        sql = f"""
            -- 1. проверяем наличие (select по трем таблицам, ru и user_id=0)
            select en, t.word_id wid, ru, ut.user_id uid, ut.translate_id tid
            from users_translates ut, translates t, words w
            where ut.translate_id = t.translate_id 
                and t.word_id = w.word_id 
                and ut.user_id = {uid} 
                and w.ru = '{word}'
            order by ru, t.translate_id DESC;
            """
        with conn.cursor() as cur:
            cur.execute(sql)
            rowcount = cur.rowcount
            fa = cur.fetchone()
        # если есть слово
        if rowcount:
            return (4, fa[0])
        return (0, None)

    # Если вызов с переводом
    with conn.cursor() as cur:
        sql = f"""
            insert into words (ru) values ('{word}')
            --ON CONFLICT (ru) DO NOTHING 
            """
        try:
            cur.execute(sql)
        except Exception as e:
            print(e)
        rowcount = cur.rowcount
    conn.commit()

    with conn.cursor() as cur:
        sql = f"""
            select word_id, ru
            from words
            where ru = '{word}';
            """
        cur.execute(sql)
        rowcount = cur.rowcount
        fa = cur.fetchone()
        word_id = fa[0]

    with conn.cursor() as cur:
        sql = f"""
            select ut.translate_id tid,  en, t.word_id wid, ru, ut.user_id uid
            from users_translates ut, translates t, words w
            where
                w.word_id = {word_id} 
                and t.word_id = {word_id} 
                and w.ru = '{word}'
                --and t.en = '{en}'
                and ut.translate_id = t.translate_id 
                and ut.user_id = {uid}
            """
        cur.execute(sql)
        rowcount = cur.rowcount
        fa = cur.fetchone()

    if rowcount:
        tid = fa[0]
        with conn.cursor() as cur:
            sql = f"""
                delete from users_translates
                where user_id = {uid} and translate_id = {tid};
            """
            try:
                cur.execute(sql)
            except Exception as e:
                print(e)
            rowcount = cur.rowcount
        conn.commit()

        with conn.cursor() as cur:
            sql = f"""
                delete from translates
                where word_id = {word_id} and translate_id = {tid};
            """
            try:
                cur.execute(sql)
            except Exception as e:
                print(e)
            rowcount = cur.rowcount
        conn.commit()

    # вставляем перевод и связь
    with conn.cursor() as cur:
        sql = f"""
            insert into translates (word_id, en) values ('{word_id}','{en}')
            """
        try:
            cur.execute(sql)
        except Exception as e:
            print(e)
        rowcount = cur.rowcount
    conn.commit()

    with conn.cursor() as cur:
        sql = f"""
            select translate_id, en
            from translates
            where word_id = '{word_id}' and en = '{en}';
            """
        cur.execute(sql)
        rowcount = cur.rowcount
        fa = cur.fetchone()
        tid = fa[0]

    # вставляем перевод и связь
    with conn.cursor() as cur:
        sql = f"""
            insert into users_translates (user_id, translate_id) values ('{uid}','{tid}')
            """
        try:
            cur.execute(sql)
        except Exception as e:
            print(e)
        rowcount = cur.rowcount
    conn.commit()

    with conn.cursor() as cur:
        sql = f"""
            select translate_id, user_id
            from users_translates
            where translate_id = '{tid}' and user_id = '{uid}';
            """
        cur.execute(sql)
        rowcount = cur.rowcount
        fa = cur.fetchone()
        tid = fa[0]
    return (0,)


def get_words(uid):
    conn = connect()
    with conn.cursor() as cur:
        cur.execute(
            f"""
            select distinct on(ru) ru, en, d.user_id as del, ut.user_id uid, ut.translate_id tid, t.word_id wid
            from users_translates ut, translates t, words w
            left join deleted d on d.user_id = {uid} and d.word_id = w.word_id
            where ut.translate_id = t.translate_id 
                and t.word_id = w.word_id
                and (ut.user_id = 0 or ut.user_id = {uid})
            order by ru, t.translate_id DESC
            ;
            """
        )
        fa = cur.fetchall()
        all = set()
        for f in fa:  # извлечь все строки
            all.add(f[1])

        cur.execute(
            f"""
            select distinct on(ru) ru, en, d.user_id as del, ut.user_id uid, ut.translate_id tid, t.word_id wid
            from users_translates ut, translates t, words w
            left join deleted d on d.user_id = {uid} and d.word_id = w.word_id
            where ut.translate_id = t.translate_id 
                and t.word_id = w.word_id
                and (ut.user_id = 0 or ut.user_id = {uid})
            order by ru, t.translate_id DESC
            ;
            """
        )
        fa = cur.fetchall()
        fa_ = []
        for t in fa:
            if not t[2]:
                fa_.append(t)
        for t in fa_:
            pass
        for t in fa_:
        ru = fa_[0][0]
        fa_ = [[item[0], item[1]] for item in fa_]
        return fa_, all

    conn.close()


if __name__ == "__main__":
    get_words(1757532608)

