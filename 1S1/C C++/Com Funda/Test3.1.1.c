#include <stdio.h>

int main(){
    char str[50], substr[20] = {}, newstr[20]= {};
    char *p;


    scanf ("%s", str);

    p = str;

    int max = 0, temp = 0, i = 0;

    while(*p != '\0'){
         if(*p != 'a' && *p != 'e' && *p != 'i' && *p != 'o' && *p != 'u')
         {
            substr[i] = *p;
            temp += 1;
            p++;
            i++;
         }
         else{
            if(temp > max){
                max = temp;
                for(int j = 0 ; j < max; j++){
                    newstr[j] = substr[j];
                }
                substr[0] = '\0';
                i = 0;
            }
            temp = 0;
            p++;
         }
    }
    printf("%s" ,newstr);
}
