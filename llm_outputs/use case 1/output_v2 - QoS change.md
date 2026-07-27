student@Ubuntu-Open5GS:~/NetSight Thesis/netsight$ ./start.sh 
Running pre-flight checks...
Container netsight-check-prerequisites-run-f771125d8720 Creating 
Container netsight-check-prerequisites-run-f771125d8720 Created 
==================================================
NetSight — Pre-flight Checks
==================================================
Checking environment variables...
  LLM_MODEL = gemma4:31b
  LLM_HOST = 192.168.100.50
  LLM_PORT = 11434
  PROMPT_FILE = prompts/system_prompt.md
  ATTACHMENTS_DIR = attachments
  OUTPUT_FILE = output/interfaces.md
[OK] All required environment variables are set.
[....] Checking LLM connectivity at http://192.168.100.50:11434 ...
[OK] LLM endpoint reachable at http://192.168.100.50:11434
[....] Checking if model 'gemma4:31b' is loaded in Ollama...
[OK] Model 'gemma4:31b' found in Ollama.
==================================================
All checks passed.

Starting NetSight agent...
Container netsight-netsight-agent-run-eacf06883387 Creating 
Container netsight-netsight-agent-run-eacf06883387 Created 
2026-07-27 15:05:34 [INFO] Log file: /app/logs/netsight_2026-07-27_15-05-34.log
2026-07-27 15:05:34 [INFO] Model: gemma4:31b
2026-07-27 15:05:34 [INFO] Host: 192.168.100.50:11434
2026-07-27 15:05:34 [INFO] Loading prompt from: prompts/system_prompt.md
2026-07-27 15:05:34 [INFO] Loading attachments from: attachments
2026-07-27 15:05:34 [INFO]   Rendering PDF: ltemme.pdf
2026-07-27 15:05:34 [WARNING]   PDF 'ltemme.pdf' has 123 pages — this will generate 123 images. Consider trimming the PDF to relevant pages.
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_001.png (48 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_002.png (228 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_003.png (204 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_004.png (125 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_005.png (339 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_006.png (253 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_007.png (142 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_008.png (289 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_009.png (322 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_010.png (188 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_011.png (239 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_012.png (291 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_013.png (369 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_014.png (356 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_015.png (311 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_016.png (329 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_017.png (401 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_018.png (371 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_019.png (416 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_020.png (338 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_021.png (314 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_022.png (343 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_023.png (339 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_024.png (342 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_025.png (308 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_026.png (341 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_027.png (363 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_028.png (318 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_029.png (354 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_030.png (370 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_031.png (357 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_032.png (366 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_033.png (353 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_034.png (359 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_035.png (324 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_036.png (271 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_037.png (267 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_038.png (253 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_039.png (327 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_040.png (339 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_041.png (376 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_042.png (339 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_043.png (326 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_044.png (272 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_045.png (347 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_046.png (370 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_047.png (353 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_048.png (347 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_049.png (349 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_050.png (312 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_051.png (302 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_052.png (313 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_053.png (364 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_054.png (303 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_055.png (303 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_056.png (334 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_057.png (368 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_058.png (424 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_059.png (273 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_060.png (291 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_061.png (251 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_062.png (254 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_063.png (299 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_064.png (275 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_065.png (357 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_066.png (390 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_067.png (388 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_068.png (330 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_069.png (340 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_070.png (329 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_071.png (309 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_072.png (314 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_073.png (327 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_074.png (357 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_075.png (326 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_076.png (288 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_077.png (298 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_078.png (318 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_079.png (262 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_080.png (297 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_081.png (310 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_082.png (265 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_083.png (342 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_084.png (329 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_085.png (270 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_086.png (277 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_087.png (275 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_088.png (305 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_089.png (328 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_090.png (343 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_091.png (336 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_092.png (324 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_093.png (336 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_094.png (164 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_095.png (108 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_096.png (125 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_097.png (140 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_098.png (110 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_099.png (81 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_100.png (198 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_101.png (304 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_102.png (348 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_103.png (325 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_104.png (374 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_105.png (342 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_106.png (308 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_107.png (314 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_108.png (291 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_109.png (151 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_110.png (327 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_111.png (219 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_112.png (248 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_113.png (51 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_114.png (194 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_115.png (50 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_116.png (307 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_117.png (349 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_118.png (337 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_119.png (348 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_120.png (229 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_121.png (65 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_122.png (227 KB)
2026-07-27 15:05:44 [INFO]     Loaded (pdf->image): ltemme_page_123.png (64 KB)
2026-07-27 15:05:44 [INFO]   PDF rendered: ltemme.pdf -> 123 page(s)
2026-07-27 15:05:44 [INFO]   Loaded (text): mme_backup.cfg (7523 chars, ~2337 tokens)
2026-07-27 15:05:44 [INFO] Loaded 124 file(s): 1 text (~2337 tokens), 123 images (35880 KB)
2026-07-27 15:05:44 [INFO] Calling Ollama (model: gemma4:31b)
2026-07-27 15:09:33 [INFO] Token usage: input=36462, output=3819, total=40281
2026-07-27 15:09:33 [INFO] LLM response received: 6960 chars
2026-07-27 15:09:33 [INFO] Interface definitions written to: output/interfaces.md
2026-07-27 15:09:33 [INFO] Done. (239.2s)
student@Ubuntu-Open5GS:~/NetSight Thesis/netsight$ ./start.sh 
Running pre-flight checks...
Container netsight-check-prerequisites-run-4065d0307850 Creating 
Container netsight-check-prerequisites-run-4065d0307850 Created 
==================================================
NetSight — Pre-flight Checks
==================================================
Checking environment variables...
  LLM_MODEL = gemma4:31b
  LLM_HOST = 192.168.100.50
  LLM_PORT = 11434
  PROMPT_FILE = prompts/system_prompt.md
  ATTACHMENTS_DIR = attachments
  OUTPUT_FILE = output/interfaces.md
[OK] All required environment variables are set.
[....] Checking LLM connectivity at http://192.168.100.50:11434 ...
[OK] LLM endpoint reachable at http://192.168.100.50:11434
[....] Checking if model 'gemma4:31b' is loaded in Ollama...
[OK] Model 'gemma4:31b' found in Ollama.
==================================================
All checks passed.

Starting NetSight agent...
Container netsight-netsight-agent-run-dd761321b9aa Creating 
Container netsight-netsight-agent-run-dd761321b9aa Created 
2026-07-27 15:34:24 [INFO] Log file: /app/logs/netsight_2026-07-27_15-34-24.log
2026-07-27 15:34:24 [INFO] Model: gemma4:31b
2026-07-27 15:34:24 [INFO] Host: 192.168.100.50:11434
2026-07-27 15:34:24 [INFO] Loading prompt from: prompts/system_prompt.md
2026-07-27 15:34:24 [INFO] Loading attachments from: attachments
2026-07-27 15:34:24 [INFO]   Rendering PDF: ltemme.pdf
2026-07-27 15:34:24 [WARNING]   PDF 'ltemme.pdf' has 123 pages — this will generate 123 images. Consider trimming the PDF to relevant pages.
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_001.png (48 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_002.png (228 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_003.png (204 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_004.png (125 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_005.png (339 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_006.png (253 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_007.png (142 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_008.png (289 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_009.png (322 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_010.png (188 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_011.png (239 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_012.png (291 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_013.png (369 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_014.png (356 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_015.png (311 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_016.png (329 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_017.png (401 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_018.png (371 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_019.png (416 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_020.png (338 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_021.png (314 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_022.png (343 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_023.png (339 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_024.png (342 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_025.png (308 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_026.png (341 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_027.png (363 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_028.png (318 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_029.png (354 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_030.png (370 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_031.png (357 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_032.png (366 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_033.png (353 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_034.png (359 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_035.png (324 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_036.png (271 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_037.png (267 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_038.png (253 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_039.png (327 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_040.png (339 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_041.png (376 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_042.png (339 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_043.png (326 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_044.png (272 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_045.png (347 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_046.png (370 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_047.png (353 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_048.png (347 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_049.png (349 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_050.png (312 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_051.png (302 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_052.png (313 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_053.png (364 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_054.png (303 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_055.png (303 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_056.png (334 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_057.png (368 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_058.png (424 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_059.png (273 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_060.png (291 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_061.png (251 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_062.png (254 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_063.png (299 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_064.png (275 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_065.png (357 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_066.png (390 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_067.png (388 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_068.png (330 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_069.png (340 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_070.png (329 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_071.png (309 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_072.png (314 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_073.png (327 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_074.png (357 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_075.png (326 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_076.png (288 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_077.png (298 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_078.png (318 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_079.png (262 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_080.png (297 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_081.png (310 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_082.png (265 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_083.png (342 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_084.png (329 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_085.png (270 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_086.png (277 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_087.png (275 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_088.png (305 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_089.png (328 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_090.png (343 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_091.png (336 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_092.png (324 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_093.png (336 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_094.png (164 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_095.png (108 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_096.png (125 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_097.png (140 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_098.png (110 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_099.png (81 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_100.png (198 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_101.png (304 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_102.png (348 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_103.png (325 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_104.png (374 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_105.png (342 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_106.png (308 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_107.png (314 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_108.png (291 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_109.png (151 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_110.png (327 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_111.png (219 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_112.png (248 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_113.png (51 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_114.png (194 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_115.png (50 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_116.png (307 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_117.png (349 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_118.png (337 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_119.png (348 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_120.png (229 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_121.png (65 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_122.png (227 KB)
2026-07-27 15:34:33 [INFO]     Loaded (pdf->image): ltemme_page_123.png (64 KB)
2026-07-27 15:34:33 [INFO]   PDF rendered: ltemme.pdf -> 123 page(s)
2026-07-27 15:34:33 [INFO]   Loaded (text): mme_backup.cfg (7523 chars, ~2337 tokens)
2026-07-27 15:34:33 [INFO] Loaded 124 file(s): 1 text (~2337 tokens), 123 images (35880 KB)
2026-07-27 15:34:33 [INFO] Calling Ollama (model: gemma4:31b)
Traceback (most recent call last):
  File "/app/agent.py", line 81, in <module>
    main()
  File "/app/agent.py", line 67, in main
    response = call_llm(config, system_prompt, documents)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/providers.py", line 36, in call_llm
    with urllib.request.urlopen(req, timeout=600) as response:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/urllib/request.py", line 215, in urlopen
    return opener.open(url, data, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/urllib/request.py", line 515, in open
    response = self._open(req, data)
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/urllib/request.py", line 532, in _open
    result = self._call_chain(self.handle_open, protocol, protocol +
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/urllib/request.py", line 492, in _call_chain
    result = func(*args)
             ^^^^^^^^^^^
  File "/usr/local/lib/python3.12/urllib/request.py", line 1373, in http_open
    return self.do_open(http.client.HTTPConnection, req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/urllib/request.py", line 1348, in do_open
    r = h.getresponse()
        ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/http/client.py", line 1450, in getresponse
    response.begin()
  File "/usr/local/lib/python3.12/http/client.py", line 336, in begin
    version, status, reason = self._read_status()
                              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/http/client.py", line 297, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/socket.py", line 720, in readinto
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^
TimeoutError: timed out
student@Ubuntu-Open5GS:~/NetSight Thesis/netsight$ ./start.sh 
Running pre-flight checks...
Container netsight-check-prerequisites-run-850188d463b2 Creating 
Container netsight-check-prerequisites-run-850188d463b2 Created 
==================================================
NetSight — Pre-flight Checks
==================================================
Checking environment variables...
  LLM_MODEL = gemma4:31b
  LLM_HOST = 192.168.100.50
  LLM_PORT = 11434
  PROMPT_FILE = prompts/system_prompt.md
  ATTACHMENTS_DIR = attachments
  OUTPUT_FILE = output/interfaces.md
[OK] All required environment variables are set.
[....] Checking LLM connectivity at http://192.168.100.50:11434 ...
[OK] LLM endpoint reachable at http://192.168.100.50:11434
[....] Checking if model 'gemma4:31b' is loaded in Ollama...
[OK] Model 'gemma4:31b' found in Ollama.
==================================================
All checks passed.

Starting NetSight agent...
Container netsight-netsight-agent-run-1a2b65ea60ff Creating 
Container netsight-netsight-agent-run-1a2b65ea60ff Created 
2026-07-27 15:55:19 [INFO] Log file: /app/logs/netsight_2026-07-27_15-55-19.log
2026-07-27 15:55:19 [INFO] Model: gemma4:31b
2026-07-27 15:55:19 [INFO] Host: 192.168.100.50:11434
2026-07-27 15:55:19 [INFO] Loading prompt from: prompts/system_prompt.md
2026-07-27 15:55:19 [INFO] Loading attachments from: attachments
2026-07-27 15:55:19 [INFO]   Rendering PDF: ltemme.pdf
2026-07-27 15:55:19 [WARNING]   PDF 'ltemme.pdf' has 123 pages — this will generate 123 images. Consider trimming the PDF to relevant pages.
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_001.png (48 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_002.png (228 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_003.png (204 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_004.png (125 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_005.png (339 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_006.png (253 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_007.png (142 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_008.png (289 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_009.png (322 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_010.png (188 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_011.png (239 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_012.png (291 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_013.png (369 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_014.png (356 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_015.png (311 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_016.png (329 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_017.png (401 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_018.png (371 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_019.png (416 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_020.png (338 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_021.png (314 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_022.png (343 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_023.png (339 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_024.png (342 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_025.png (308 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_026.png (341 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_027.png (363 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_028.png (318 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_029.png (354 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_030.png (370 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_031.png (357 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_032.png (366 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_033.png (353 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_034.png (359 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_035.png (324 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_036.png (271 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_037.png (267 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_038.png (253 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_039.png (327 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_040.png (339 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_041.png (376 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_042.png (339 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_043.png (326 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_044.png (272 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_045.png (347 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_046.png (370 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_047.png (353 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_048.png (347 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_049.png (349 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_050.png (312 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_051.png (302 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_052.png (313 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_053.png (364 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_054.png (303 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_055.png (303 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_056.png (334 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_057.png (368 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_058.png (424 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_059.png (273 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_060.png (291 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_061.png (251 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_062.png (254 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_063.png (299 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_064.png (275 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_065.png (357 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_066.png (390 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_067.png (388 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_068.png (330 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_069.png (340 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_070.png (329 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_071.png (309 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_072.png (314 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_073.png (327 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_074.png (357 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_075.png (326 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_076.png (288 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_077.png (298 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_078.png (318 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_079.png (262 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_080.png (297 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_081.png (310 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_082.png (265 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_083.png (342 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_084.png (329 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_085.png (270 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_086.png (277 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_087.png (275 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_088.png (305 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_089.png (328 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_090.png (343 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_091.png (336 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_092.png (324 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_093.png (336 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_094.png (164 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_095.png (108 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_096.png (125 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_097.png (140 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_098.png (110 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_099.png (81 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_100.png (198 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_101.png (304 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_102.png (348 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_103.png (325 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_104.png (374 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_105.png (342 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_106.png (308 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_107.png (314 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_108.png (291 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_109.png (151 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_110.png (327 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_111.png (219 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_112.png (248 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_113.png (51 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_114.png (194 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_115.png (50 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_116.png (307 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_117.png (349 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_118.png (337 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_119.png (348 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_120.png (229 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_121.png (65 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_122.png (227 KB)
2026-07-27 15:55:28 [INFO]     Loaded (pdf->image): ltemme_page_123.png (64 KB)
2026-07-27 15:55:28 [INFO]   PDF rendered: ltemme.pdf -> 123 page(s)
2026-07-27 15:55:28 [INFO]   Loaded (text): mme_backup.cfg (7523 chars, ~2337 tokens)
2026-07-27 15:55:28 [INFO] Loaded 124 file(s): 1 text (~2337 tokens), 123 images (35880 KB)
2026-07-27 15:55:28 [INFO] Calling Ollama (model: gemma4:31b)
2026-07-27 15:58:32 [INFO] Token usage: input=36642, output=2354, total=38996
2026-07-27 15:58:32 [INFO] LLM response received: 3677 chars
2026-07-27 15:58:32 [INFO] Interface definitions written to: output/interfaces.md
2026-07-27 15:58:32 [INFO] Done. (193.7s)

