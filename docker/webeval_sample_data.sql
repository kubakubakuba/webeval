--
-- PostgreSQL database dump
--

\restrict foIUOY3mMGd1BRc6qNBMf9JvFAcIWUvn2iGXFgCfDbnMnhCOz8RUf3sVVr6Hh9y

-- Dumped from database version 13.22
-- Dumped by pg_dump version 13.22

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: qtrvsim
--

COPY public.tasks (id, name, path, available, sequence) FROM stdin;
1	Simple addition	addition.toml	t	1
2	Read and write into memory	readmem.toml	t	2
3	Bubble sort	bubble.toml	t	3
8	Vector sum	sum.toml	t	4
4	Cache optimization	cache.toml	t	5
13	Fibonacci sequence without the hazard unit	fibonacci.toml	t	6
5	Data hazard prevention	hazards.toml	t	7
6	Print hexadecimal to serial port	uart.toml	t	8
7	Simple calculator	calculator.toml	t	9
9	Matrix multiplication	matrix.toml	f	10
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: qtrvsim
--

COPY public.users (id, email, password, salt, token, verified, username, admin, display_name, country, organization, "group", visibility, can_submit, user_api_key, user_api_key_expiry) FROM stdin;
bfe11ab0-f288-418e-bbc6-ba59617556b5	b152eb9851e2ed73b27f888c2613de5435e25a18ae5638fb17c52468fd0247c55770541ed4bbad7bd699f75159c02bd6c562ab6ff2f3fdb2862be465d31d1fbc	cb7d0569eddff00a2a4c0eb4a18ffc594da40e59f97ea306eb27b0afa9ea3b314417a8dc2f8841da358f1371df840359f9d55316be64bf2b2c8c7930e0c47f36	793492cec4dd88c16437fef86c51fb9b	\N	t	test	f	\N	\N	\N	\N	0	0	\N	\N
6e191f30-747c-4df2-a31b-3ac166512e73	f3be085dd76b5c35d62772424a7dae715d4e1b65a62721e5d9b51b5a6b84f0242d437009814067800c12f14a1b7466e1feef72b49e002bc65f3602d38e5af6e3	d033dfdcbd24b7d6fd9b50c4e113fe043b57af7d838e5f2980469774368d819058d3e4e6e99e840ae87ac9650fb38b94f6cde4627de3f62126fcd970d94c8985	823013382590da6aceb31a6423de7d94	\N	t	admin	t	\N	\N	\N	\N	0	1	\N	\N
b121f56b-699c-48cc-8172-d89306bd8154	eb3a83a1fc66b322f1e72e41008321c59e1264319dd36897217d0d94b6b0cd02958f3006ae18668e3efe45f352c7ba8e104d28f478cfa6bfec6782434c981b14	f92b8490592dd02bf5598e9901417eca73df8fafa85fc313a28473ec01f45086c35442ebe78326694ea6f9af8c64100a508bbe4fd945f7d6822cb221e76c9d65	f1840412a28d9e417b3d82f943b9af39	\N	t	reference	f	\N	\N	\N	\N	0	1	\N	\N
\.


--
-- Data for Name: results; Type: TABLE DATA; Schema: public; Owner: qtrvsim
--

COPY public.results (userid, taskid, result_file, last_source, best_source, score_last, score_best, "time", result) FROM stdin;
b121f56b-699c-48cc-8172-d89306bd8154	1	Evaluation started on: 2025-11-16 01:03:44\nError log:\nRunning: 'test01'\n\ntest01 - PASSED\n\nRunning: 'test02'\n\ntest02 - PASSED\n\n\nEvaluation ended on: 2025-11-16 01:03:44\nResult: 10\n	//Write a program that loads a value 10 into register a1 and value 12 into register a2. Then, add the values and store the result in register a3.\n\nli a1,10\nli a2,12\nadd a3, a1, a2\n\nnop\nnop\nnop\nnop\nebreak	//Write a program that loads a value 10 into register a1 and value 12 into register a2. Then, add the values and store the result in register a3.\n\nli a1,10\nli a2,12\nadd a3, a1, a2\n\nnop\nnop\nnop\nnop\nebreak	10	10	2025-11-16 01:03:44.356082+00	0
\.


--
-- Data for Name: submissions; Type: TABLE DATA; Schema: public; Owner: qtrvsim
--

COPY public.submissions (id, userid, taskid, file, evaluated, "time") FROM stdin;
12	b121f56b-699c-48cc-8172-d89306bd8154	1	//Write a program that loads a value 10 into register a1 and value 12 into register a2. Then, add the values and store the result in register a3.\n\nli a1,10\nli a2,12\nadd a3, a1, a2\n\nnop\nnop\nnop\nnop\nebreak	t	2025-11-16 01:03:38.150787+00
\.


--
-- Data for Name: api_keys; Type: TABLE DATA; Schema: public; Owner: qtrvsim
--

COPY public.api_keys (id, key, created_by, created_at, last_used, description, active) FROM stdin;
\.


--
-- Name: api_keys_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qtrvsim
--

SELECT pg_catalog.setval('public.api_keys_id_seq', 1, false);


--
-- Name: submissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qtrvsim
--

SELECT pg_catalog.setval('public.submissions_id_seq', 20, true);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qtrvsim
--

SELECT pg_catalog.setval('public.tasks_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

\unrestrict foIUOY3mMGd1BRc6qNBMf9JvFAcIWUvn2iGXFgCfDbnMnhCOz8RUf3sVVr6Hh9y

