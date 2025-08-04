user_memory = {
    "name": "felix",
    "price": None,
    "color": None,
}



def clean_none_fields(memory):
    cleaned_list = {}
    for i in memory:
        if memory[i] is not None:
            cleaned_list.update({i: memory[i]})
    return (cleaned_list)


res = clean_none_fields(user_memory)
    


print(res)
