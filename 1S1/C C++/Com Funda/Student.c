#include <stdio.h>

struct Student
{
    int ID;
    char Name[100];
    int Age;
};

int main()
{
    struct Student S1[3];
    int number = 3;
    for(int i=0; i<number; i++)
    {
        printf("Student%d ID = ", i+1);
        scanf("%d", &S1[i].ID);
        printf("Student%d Name = ", i+1);
        scanf("%s", S1[i].Name);
        printf("Student%d Age = ", i+1);
        scanf("%d", &S1[i].Age);
    }

    printf("\n");

    for(int i=0; i<number; i++)
    {
        printf("Student%d = %d %s %d\n", i+1, S1[i].ID, S1[i].Name, S1[i].Age);
    }

    return 0;
}
