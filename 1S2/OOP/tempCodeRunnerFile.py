for transaction in account.transaction_list:
                print("Type : {}, Amount : {}, Balance : {}".format(transaction.transaction_type, transaction.amount_in, transaction.total), end ="")
                if transaction.target_account:
                    print(", Target : {}".format(transaction.target_account.user.name), end = "")
                print()
            print("")