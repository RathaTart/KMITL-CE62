// // Case Study 01 - Multithreading 
// // Updated: 2025-06-25
// using System;
// using System.IO;
// using CalculatingFunctions;
// using System.Threading;
// using System;
// using System.Text.Json;
// using System.Diagnostics;

// class Program
// {
//     static decimal[] data = new decimal[11000001];
//     static decimal result = 0;
//     static int index = 0;

//     //Algorithm of CalClass.Calculate1()
//     //{        

//     //    index = 0;
//     //    while (index < 110000000) 
//     //    {
//     //        decimal sum = 0;


//     //        if ((int)data[index] % 2 == 0)
//     //        {
//     //            sum += (decimal)((double)data[index] * 0.002);
//     //        }
//     //        else if ((int)data[index] % 3 == 0)
//     //        {
//     //            sum += (decimal)((double)data[index] * 0.003);
//     //        }
//     //        else if ((int)data[index] % 5 == 0)
//     //        {
//     //            sum += (decimal)((double)data[index] * 0.005);
//     //        }
//     //        else if ((int)data[index] % 7 == 0)
//     //        {
//     //            sum += (decimal)((double)data[index] * 0.007);
//     //        }
//     //        else
//     //        {
//     //            sum += (decimal)((double)data[index] * 0.001);
//     //        }


//     //        if ((long)sum % 2 == 0)
//     //        {
//     //            result += sum * (decimal)0.00001;
//     //        }
//     //        else
//     //        {
//     //            result += (sum * (-1)) * (decimal)0.00001;
//     //        }

//     //        data[index] *= (decimal)0.1;
//     //        index++;

//     //    }
//     //}

//     static void ThreadWork(int start, int end, int tid, decimal[] partial, CalClass cf)
//     {
//         int idx = start;      // index ส่วนของเธรดนี้
//         decimal local = 0m;
//         while (idx < end)
//         {
//             local += cf.Calculate1(ref data, ref idx);
//         }
//         partial[tid] = local; // ส่งผลรวมของช่วงนี้ออกมา
//     }




//     private static void LoadData()
//     {
//         Console.WriteLine("Loading data...");
//         FileStream fs = new FileStream("data.bin", FileMode.Open);
//         BinaryReader br = new BinaryReader(fs);
//         for (int i = 0; i < data.Length; i++)
//         {
//             Single f = br.ReadSingle();
//             data[i] = (decimal)(f * 36);
//         }
//         Console.WriteLine("Data loaded successfully.\n\n");
//     }


//     private static void Main(string[] args)
//     {
//         LoadData();

//         int n = Math.Min(10_000_000, data.Length);
//         int cpu = Environment.ProcessorCount;
//         int T = (cpu < 2) ? 2 : (cpu > 16 ? 16 : cpu);   // แทน Math.Clamp ถ้าไม่มี

//         // สร้าง CalClass ประจำ "ช่องเธรด" (คงตัวตลอด 30 รอบ)
//         var cfs = new CalClass[T];
//         for (int t = 0; t < T; t++) cfs[t] = new CalClass();

//         int chunk = n / T;
//         int remainder = n % T;

//         Console.WriteLine($"Calculation start ... (n={n}, threads={T})");
//         var sw = Stopwatch.StartNew();

//         decimal result = 0m;
//         const int ROUNDS = 30;

//         for (int round = 0; round < ROUNDS; round++)
//         {
//             var threads = new Thread[T];
//             var partial = new decimal[T];

//             int start = 0;
//             for (int t = 0; t < T; t++)
//             {
//                 int size = chunk + (t < remainder ? 1 : 0);
//                 int s = start;
//                 int e = s + size;
//                 int tid = t;
//                 start = e;

//                 var th = new Thread(() => ThreadWork(s, e, tid, partial, cfs[tid]));
//                 th.IsBackground = false;
//                 th.Priority = ThreadPriority.AboveNormal;
//                 threads[t] = th;
//                 th.Start();
//             }

//             for (int t = 0; t < T; t++) threads[t].Join();

//             // สะสมผลของ "รอบนี้" เข้า result เหมือนโค้ดเดิม
//             for (int t = 0; t < T; t++) result += partial[t];
//         }

//         sw.Stop();
//         Console.WriteLine($"Calculation finished in {sw.ElapsedMilliseconds} ms. Result: {result:F25}");
//     }

// }