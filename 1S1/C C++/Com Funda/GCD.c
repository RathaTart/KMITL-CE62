
#include <stdio.h>

int main(void) {
  int num1, num2;
  int GCD;
  int min;
  printf("Enter first number : ");
  scanf("%d", &num1);
  printf("Enter second number : ");
  scanf("%d", &num2);
  if(num1>num2)
  {
    min = num2;
  }
  else
  {
    min = num1;
  }
  for(int i=1; i<=min; i++)
    {
      if((num1%i == 0)&&(num2%i == 0))
      {
        GCD = i;
      }
    }
  printf("Greatest common divisor = %d", GCD);

  return 0;
}
