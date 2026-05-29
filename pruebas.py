def validaciones(email):
    

    if not email.isalpha():
        return "necesita llevar letras"

    
m = "123-"
print(validaciones(m))

#print("contador: ", len(m))
