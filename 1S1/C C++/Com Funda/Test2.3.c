#include <stdio.h>
#include <math.h>

int main()
{
    float x1, y1, x2, y2, x3, y3;
    scanf("%f %f %f %f %f %f", &x1, &y1, &x2, &y2, &x3, &y3);
    float len = 0.000;

    len = sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2) ) + sqrt( (x2-x3)*(x2-x3) + (y2-y3)*(y2-y3) ) + sqrt( (x3-x1)*(x3-x1) + (y3-y1)*(y3-y1) );

    printf("%.3f", len);

    return 0;
}
