// // Benchmark multi-thread counts (no library, Thread only)
// // Build: Release x64 แนะนำ
// using System;
// using System.IO;
// using System.Diagnostics;
// using System.Threading;
// using CalculatingFunctions;

// class Program
// {
//     // ข้อมูลต้นฉบับ (master) กับชุดที่ใช้คำนวณ (work)
//     static decimal[] masterData = new decimal[11000001];
//     static decimal[] data       = new decimal[11000001];

//     const int N_TARGET = 10_000_000;  // จำนวนรายการที่โจทย์ใช้
//     const int ROUNDS   = 30;          // ทำครบ 30 รอบแบบเดิม

//     static void LoadMasterData()
//     {
//         Console.WriteLine("Loading data...");
//         using var fs = new FileStream("data.bin", FileMode.Open, FileAccess.Read, FileShare.Read);
//         using var br = new BinaryReader(fs);
//         for (int i = 0; i < masterData.Length; i++)
//         {
//             float f = br.ReadSingle();
//             masterData[i] = (decimal)(f * 36f);
//         }
//         Console.WriteLine("Data loaded successfully.\n");
//     }

//     // คัดลอก master → data เพื่อให้ “แต่ละการทดลอง T” เริ่มจากข้อมูลเดียวกัน (แฟร์)
//     static void ResetWorkData()
//     {
//         Array.Copy(masterData, data, masterData.Length);
//     }

//     // ทำงานช่วงหนึ่งรอบของเธรดเดียว (ไม่แชร์ index กัน, ไม่ล็อก)
//     static void ThreadWork(int start, int end, int tid, decimal[] partial, CalClass cf)
//     {
//         int idx = start;
//         decimal local = 0m;
//         while (idx < end)
//         {
//             local += cf.Calculate1(ref data, ref idx);
//         }
//         partial[tid] = local;
//     }

//     // รันครบ 30 รอบด้วยจำนวนเธรด T แล้วคืน (เวลา, ผลลัพธ์)
//     static (long ms, decimal result) RunWithThreads(int T)
//     {
//         ResetWorkData(); // เริ่มจากข้อมูลเดิมเสมอสำหรับค่าทดสอบนี้

//         int n = Math.Min(N_TARGET, data.Length);

//         // เตรียมแบ่งงานเท่า ๆ กัน
//         int chunk = n / T;
//         int remainder = n % T;

//         // สร้าง CalClass ประจำช่องเธรด (คงตัวตลอด 30 รอบ)
//         var cfs = new CalClass[T];
//         for (int t = 0; t < T; t++) cfs[t] = new CalClass();

//         decimal result = 0m;
//         var sw = Stopwatch.StartNew();

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

//             // สะสมผลของรอบนี้
//             for (int t = 0; t < T; t++) result += partial[t];
//         }

//         sw.Stop();
//         return (sw.ElapsedMilliseconds, result);
//     }

//     // อุ่น JIT เบา ๆ ให้ผลการเทียบเสถียรกว่า
//     static void Warmup()
//     {
//         var cf = new CalClass();
//         int idx = 0;
//         for (int k = 0; k < 1000 && idx < 5000; k++)
//         {
//             cf.Calculate1(ref data, ref idx);
//         }
//     }

//     static void Main(string[] args)
//     {
//         LoadMasterData();

//         // เลือกชุดค่า T ที่จะทดสอบ (1..min(16, 2*logicalCPU))
//         int logical = Environment.ProcessorCount;
//         int maxT = Math.Min(32, Math.Max(1, logical * 2));
//         // ถ้าอยากระบุเองผ่าน args: --tlist=1,2,4,8,12
//         int[] candidates = null;
//         foreach (var a in args)
//         {
//             if (a.StartsWith("--tlist="))
//             {
//                 var part = a.Substring(8).Split(',');
//                 var list = new System.Collections.Generic.List<int>();
//                 foreach (var p in part)
//                     if (int.TryParse(p.Trim(), out var v) && v > 0) list.Add(v);
//                 candidates = list.ToArray();
//             }
//         }
//         if (candidates == null)
//         {
//             // ดีฟอลต์: 1..logical แล้วต่อด้วย logical+1..maxT (ไม่ซ้ำ)
//             var tmp = new System.Collections.Generic.List<int>();
//             for (int t = 1; t <= logical; t++) tmp.Add(t);
//             for (int t = logical + 1; t <= maxT; t++) tmp.Add(t);
//             candidates = tmp.ToArray();
//         }

//         // อุ่น JIT
//         ResetWorkData();
//         Warmup();

//         Console.WriteLine($"Logical CPUs = {logical}");
//         Console.WriteLine($"Testing thread counts: {string.Join(", ", candidates)}\n");

//         // หัวตาราง
//         Console.WriteLine("T\tTime(ms)\tResult");
//         Console.WriteLine("-----------------------------------------------");

//         long bestMs = long.MaxValue;
//         int bestT = -1;
//         decimal refResult = 0m;

//         for (int i = 0; i < candidates.Length; i++)
//         {
//             int T = candidates[i];
//             var (ms, result) = RunWithThreads(T);

//             if (i == 0) refResult = result; // อ้างอิงค่าผลลัพธ์
//             // แสดงผล
//             Console.WriteLine($"{T}\t{ms}\t\t{result:F25}");

//             if (ms < bestMs) { bestMs = ms; bestT = T; }
//         }

//         Console.WriteLine("-----------------------------------------------");
//         Console.WriteLine($"Best T = {bestT}  →  {bestMs} ms");
//         Console.WriteLine($"Reference Result ≈ {refResult:F25}");
//         Console.WriteLine("\nNote: ผลลัพธ์ทุกแถวควรใกล้เคียงกัน (ต่างเล็กน้อยได้จากลำดับ floating/decimal).");
//     }
// }
