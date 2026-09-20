// Online C compiler to run C program online
#include <stdio.h>

#include <string.h>

int main() {

  char a[100];
  char b[100];
  int found = 0;
  int count = 0;
  int num = 0;
  int d, e;


  scanf("%[^\n]%*c", a);
  scanf("%[^\n]%*c", b);

  for(int i = 0;i < strlen(a); i++){
      if(a[i] == b[count]){
          count++;
          num++;
          if(num==strlen(b)){
              printf("%d", i - strlen(b) + 1);
              found = 1;
          }
      }
      else{
          count = 0;
          num = 0;
      }
  }he
    if(found == 0){
        printf("-1");
    }

  return 0;
}
