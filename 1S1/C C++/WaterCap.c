#include<stdio.h>

int main(){

    int initial, exceed, exchange, input, output, a;
    scanf("%d", &input);
    initial = (input/5)*5;
//    printf("INPUT : %d\nInitial : %d\n", input, initial);
    exceed = input%5;
    while(input>=5){
        exchange = input/5 + exchange + a;
        a = (input/5)%5 ;
        input = input/5;
        //printf("GET IN");
    }

    output = initial + exceed + exchange - a;

    printf("%d", output);

    return 0;

}
//1234
//1542
