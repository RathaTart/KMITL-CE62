#include <stdio.h>
#include <string.h>
#include <stdbool.h>


int main()
{
    int m,n;

    scanf("%d", &m);
    scanf("%d", &n);

    int matrix[2*m+1][2*m+1];
    int *p1, *p2, *p3, *p4;
    p1 = &matrix[m][m];
    p2 = &matrix[m][m];
    p3 = &matrix[m][m];
    p4 = &matrix[m][m];

    // Initialize 2D array with 0
    memset(matrix, 0, sizeof(matrix));
    matrix[m][m] = n;

    int num = (2*m+1)*(2*m+1)/4;

//---------------------------------UP LEFT-----------------------------------//

    int num_run = 0;
    int direction = 0;
    int miniLoopCount = 0;
    int m_temp = m;
    bool firstTime = true;

    for(int num_count=0; num_count<num; num_count++)
    {
        miniLoopCount++;

        // UP
        if(direction == 0)
        {
            p1 = p1 - (2*m+1);
            num_run++;
            *p1 = (n + num_run)%10;
        }

        // Left
        if(direction == 1)
        {
            p1--;
            *p1 = (n + num_run)%10;
        }

        // DOWN
        if(direction == 2)
        {
            p1 = p1 + (2*m+1);
            *p1 = (n + num_run)%10;
        }

        // Right
        if(direction == 3)
        {
            p1++;
            num_run--;
            *p1 = (n + num_run)%10;
        }

        if((miniLoopCount == m_temp) && (firstTime == true))
        {
            direction = (direction+1)%4;
            firstTime = false;
            miniLoopCount = 0;
        }
        else if((miniLoopCount == m_temp) && (firstTime == false))
        {
            direction = (direction+1)%4;
            m_temp--;
            firstTime = true;
            miniLoopCount = 0;
        }
    }

//-------------------------------------DOWN LEFT-------------------------------------//

    num_run = 0;
    direction = 0;
    miniLoopCount = 0;
    m_temp = m;
    firstTime = true;

    for(int num_count=0; num_count<num; num_count++)
    {
        miniLoopCount++;

        // Left
        if(direction == 0)
        {
            p2--;
            num_run++;
            *p2 = (n + num_run)%10;
        }

        // DOWN
        if(direction == 1)
        {
            p2 = p2 + (2*m+1);
            *p2 = (n + num_run)%10;
        }

        // Right
        if(direction == 2)
        {
            p2++;
            *p2 = (n + num_run)%10;
        }

        // UP
        if(direction == 3)
        {
            p2 = p2 - (2*m+1);
            num_run--;
            *p2 = (n + num_run)%10;
        }

        if((miniLoopCount == m_temp) && (firstTime == true))
        {
            direction = (direction+1)%4;
            firstTime = false;
            miniLoopCount = 0;
        }
        else if((miniLoopCount == m_temp) && (firstTime == false))
        {
            direction = (direction+1)%4;
            m_temp--;
            firstTime = true;
            miniLoopCount = 0;
        }
    }

//-------------------------------------DOWN RIGHT-------------------------------------//

    num_run = 0;
    direction = 0;
    miniLoopCount = 0;
    m_temp = m;
    firstTime = true;

    for(int num_count=0; num_count<num; num_count++)
    {
        miniLoopCount++;

        // DOWN
        if(direction == 0)
        {
            p3 = p3 + (2*m+1);
            num_run++;
            *p3 = (n + num_run)%10;
        }

        // Right
        if(direction == 1)
        {
            p3++;
            *p3 = (n + num_run)%10;
        }

        // UP
        if(direction == 2)
        {
            p3 = p3 - (2*m+1);
            *p3 = (n + num_run)%10;
        }

        // Left
        if(direction == 3)
        {
            p3--;
            num_run--;
            *p3 = (n + num_run)%10;
        }

        if((miniLoopCount == m_temp) && (firstTime == true))
        {
            direction = (direction+1)%4;
            firstTime = false;
            miniLoopCount = 0;
        }
        else if((miniLoopCount == m_temp) && (firstTime == false))
        {
            direction = (direction+1)%4;
            m_temp--;
            firstTime = true;
            miniLoopCount = 0;
        }
    }

//-------------------------------------UP RIGHT-------------------------------------//

    num_run = 0;
    direction = 0;
    miniLoopCount = 0;
    m_temp = m;
    firstTime = true;

    for(int num_count=0; num_count<num; num_count++)
    {
        miniLoopCount++;

        // Right
        if(direction == 0)
        {
            p4++;
            num_run++;
            *p4 = (n + num_run)%10;
        }

        // UP
        if(direction == 1)
        {
            p4 = p4 - (2*m+1);
            *p4 = (n + num_run)%10;
        }

        // Left
        if(direction == 2)
        {
            p4--;
            *p4 = (n + num_run)%10;
        }

        // DOWN
        if(direction == 3)
        {
            p4 = p4 + (2*m+1);
            num_run--;
            *p4 = (n + num_run)%10;
        }

        if((miniLoopCount == m_temp) && (firstTime == true))
        {
            direction = (direction+1)%4;
            firstTime = false;
            miniLoopCount = 0;
        }
        else if((miniLoopCount == m_temp) && (firstTime == false))
        {
            direction = (direction+1)%4;
            m_temp--;
            firstTime = true;
            miniLoopCount = 0;
        }
    }

    for (int i = 0; i < 2*m+1; i++)
    {
        for (int j = 0; j < 2*m+1; j++) {
            printf("%d", matrix[i][j]);
        }
        printf("\n");
    }

    return 0;
}
