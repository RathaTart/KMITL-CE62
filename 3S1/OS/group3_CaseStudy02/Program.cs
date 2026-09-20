using System;
using System.Threading;

namespace OS_Problem_02
{
    class Thread_safe_buffer
    {
        static int[] TSBuffer = new int[10];
        static int Front = 0;
        static int Back = 0;
        static int Count = 0;

        static readonly object qlock = new object();
        static volatile int producersAlive = 2;
        static volatile bool producersDone = false;

        static void EnQueue(int eq)
        {
            lock (qlock)
            {
                while (Count == TSBuffer.Length)
                {
                    string who = Thread.CurrentThread.Name ?? $"P-{Thread.CurrentThread.ManagedThreadId}";
                    Console.WriteLine("[{0}]: Queue full, waiting........", who);
                    Monitor.Wait(qlock);
                }

                TSBuffer[Back] = eq;
                Back = (Back + 1) % TSBuffer.Length;
                Count++;

                Monitor.PulseAll(qlock);
            }
        }

        static bool DeQueue(int consumerId, out int value)
        {
            lock (qlock)
            {
                while (Count == 0)
                {
                    if (producersDone) { value = default; return false; }
                    Console.WriteLine("[Thread-{0}]: Queue empty, waiting........", consumerId);
                    Monitor.Wait(qlock);
                }

                value = TSBuffer[Front];
                Front = (Front + 1) % TSBuffer.Length;
                Count--;

                Monitor.PulseAll(qlock);
                return true;
            }
        }

        static void ProducerDoneSignal()
        {
            if (Interlocked.Decrement(ref producersAlive) == 0)
            {
                lock (qlock)
                {
                    producersDone = true;
                    Monitor.PulseAll(qlock);
                }
            }
        }

        static void th01(object t)
        {
            if (Thread.CurrentThread.Name == null) Thread.CurrentThread.Name = "Thread-100";

            int i;
            for (i = 1; i < 51; i++)
            {
                EnQueue(i);
                Thread.Sleep(5); //ห้ามแก้ไขหรือเปลี่ยนแปลงบรรทัดนี้/Editing or Modification of this line is forbidden
            }
            ProducerDoneSignal();
        }

        static void th011(object t)
        {
            if (Thread.CurrentThread.Name == null) Thread.CurrentThread.Name = "Thread-200";

            int i;

            for (i = 100; i < 151; i++)
            {
                EnQueue(i);
                Thread.Sleep(7); //ห้ามแก้ไขหรือเปลี่ยนแปลงบรรทัดนี้/Editing or Modification of this line is forbidden
            }
            ProducerDoneSignal();
        }


        static void th02(object x)
        {
            int i, j, id;

            id = (int)x;
            for (i = 1; i < 61; i++)
            {
                if (!DeQueue(id, out j))
                {
                    break;
                }
                Console.WriteLine("j={0}, thread:{1}", j, id);
                Thread.Sleep(16); //ห้ามแก้ไขหรือเปลี่ยนแปลงบรรทัดนี้/Editing or Modification of this line is forbidden
            }
        }

        static void Main()
        {
            Thread t1 = new Thread(th01);
            Thread t11 = new Thread(th011);
            Thread t2 = new Thread(th02);
            Thread t21 = new Thread(th02);
            Thread t22 = new Thread(th02);

            t1.Start(100);
            t11.Start(200);
            t2.Start(1);
            t21.Start(2);
            t22.Start(3);

            t1.Join();
            t11.Join();

            lock (qlock) { producersDone = true; Monitor.PulseAll(qlock); }

            t2.Join();
            t21.Join();
            t22.Join();
        }
    }
}
