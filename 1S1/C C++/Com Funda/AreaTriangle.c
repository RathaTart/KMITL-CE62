#include <stdio.h>
#include <math.h>

float area(int x1, int y1, int x2, int y2, int x3, int y3)
{
    float area = (0.5)*(abs(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2)));
    return area;
}

int main()
{
    int x1, x2, x3, y1, y2, y3;
    scanf("%d %d %d %d %d %d", &x1, &y1,  &x2, &y2, &x3, &y3);
    printf("%.2f", area(x1,y1,x2,y2,x3,y3));

    return 0;
}
