#include<stdio.h>
#include<math.h>

int main(void){

    float radius, area;
    printf("Pls enter radius = ");
    scanf("%f", &radius);

    area = M_PI*pow(radius, 2);

    printf("Area = %f", area);

    /*
    char str;
    char x = getchar(str);
    printf("X = %c", x);
    */

    return 0;
}
