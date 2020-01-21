import sqlite3
import re


class table:
    def __init__(self, primary, columns, size):
        self.primary = primary
        self.columns = columns
        self.size = size


def transpose(matrix):
    return zip(*matrix)


class SqlIO:
    def __init__(self, database):
        self.database = database
        self.connect = sqlite3.connect(database)
        self.tables = {}
        self.count = 0
        self.commitlimit = 512 # commit after 512 inserts
        self.SqlRefresh()

    def SqlRefresh(self):
        # read existed tables
        sql1 = "select name from main.sqlite_master WHERE type=\'table\'"
        cursor = self.connect.cursor()
        cursor2=self.connect.cursor()
        count = cursor.execute(sql1)

        # tables=count.fetchall()
        # print(tables)
        # print(tables[0][0])  #[('QA',), ('sqlite_stat1',), ('sqlite_stat4',)]


        for row in count:
            if row[0] is not None:
                # continue
                tmp = []
                for column in cursor2.execute('PRAGMA table_info(' + str(row[0]) + ')'):
                    tmp.append(column[1])
                # self.tables[row[0]] = (tmp[0], tmp.pop(0), len(tmp) + 1)
                # self.tables[row[0]]=tuple(tmp)+(len(tmp),)
                primary=tmp.pop(0)
                self.tables[row[0]]=table(primary,tmp,len(tmp)+1)


    def SqlTableExists(self, table_name):
        # judge whether a table exists
        sql = "select name from main.sqlite_master where type = \'table\'"
        cursor = self.connect.cursor()
        count = cursor.execute(sql)
        for row in count:
            if row[0] == table_name:
                cursor.close()
                return True
        cursor.close()
        return False


    def SqlMake(self, table_name, primary, primary_len, terms, terms_len):
        # make a table
        sql = "create table " + table_name + " (" + primary + " varchar(" + str(primary_len) + ") "
        for i in terms:
            sql += ", " + i + " varchar(" + str(terms_len) + ") "
        sql += ")"
        self.tables[table_name] = (table(primary, terms, len(terms) + 1))
        cursor = self.connect.cursor()
        cursor.execute(sql)
        cursor.close()


    def SqlReader(self, table_name, column):
        # read single column
        sql = "select " + column + " from " + table_name
        cursor = self.connect.cursor()
        tmp = []
        for row in cursor.execute(sql):
            tmp.append(row[0])
        cursor.close()
        return tmp


    def SqlColumnsReader(self, table_name, columns):
        # read many columns
        tmp = []
        for i in columns:
            tmp.append(self.SqlReader(table_name, i))
        return transpose(tmp)


    def SqlInsert(self, table_name, data):
        # insert a record in dictionary form, throw exception when primary key is invalid
        sql = "insert into " + table_name + " values " + "("
        current_table = self.tables[table_name]
        sql += '?'
        for i in range(current_table.size - 1):
        # for i in range(len(current_table) - 1):
            sql += ",?"
        sql += ")"
        tmp = []
        if current_table.primary in data:
            tmp.append(data[current_table.primary])
        else:
            raise RuntimeError("null primary key")
        for i in current_table.columns:
            if i in data:
                tmp.append(data[i])
            else:
                tmp.append('null')
        cursor = self.connect.cursor()
        cursor.execute(sql, tuple(tmp))
        cursor.close()
        self.count += 1
        if self.count >= self.commitlimit:
            self.connect.commit()
            self.count = 0
        else:
            self.count += 1


    def SqlDeletetable(self, table_name):
        # add some instructions in case user deletes tables casually.

        # if self.SqlTableExists(table_name):
        #     print('The table has already existed.')
        #     print('Are yor sure to delete table: ' + table_name)
        #     print('print "yes" to comfirm deletion, otherwise deletion would be canceled.')
        #     print('----------------------------------------------------------------')
        #     delete_or_not = input()
        #     print('----------------------------------------------------------------')
        #     if delete_or_not == 'yes':
        #         drp_tb_sql = "drop table if exists " + table_name
        #         self.connect.cursor().execute(drp_tb_sql)
        #         return True
        #     else:
        #         print("Stop deleting.")
        #         print("Please check your table name.")
        #         return False
        # else:
        #     print("Table doesn't exist!")
        #     print("Please check your table name.")
        #     return False

        if self.SqlTableExists(table_name):
            drp_tb_sql = "drop table if exists " + table_name
            self.connect.cursor().execute(drp_tb_sql)
            return True
        else:
            print("Table doesn't exist!")
            print("Please check your table name.")
            return False


    def Sqlexecute(self, sql):
        # simply execute input sql and return the result
        cursor=self.connect.cursor()
        result_table=cursor.execute(sql)

        # count=0
        # for row in result_table:
        #     count+=1
        #     print(count)
        #     print(row[1])

        # print('create table')
        # sql_create='create table make_sjtu_great_again_again as select * from result_table as new'
        # self.connect.execute(sql_create)
        return result_table


    # def SqlDeleteRow(self,table_name,sql):
    #     cursor=self.connect.cursor()
    #     cursor.execute(str)


    def SqlCommit(self):
        self.connect.commit()

    def __del__(self):
        self.connect.commit()
        self.connect.close()


if __name__ == '__main__':
    database=SqlIO('sjtu.db')
    # print(database.SqlTableExists('QA_sentiment'))
    # print(database.tables['make_sjtu_great_again'].columns)

    # sql = 'select question_url,make_sjtu_great_again.question,follower,viewed,date,answers, \
    #         QA_sentiment.question,positive_prob,confidence,negative_prob,sentiment\
    #         from make_sjtu_great_again left join QA_sentiment on \
    #         make_sjtu_great_again.question=QA_sentiment.question'
    # database.Sqlexecute(sql)
