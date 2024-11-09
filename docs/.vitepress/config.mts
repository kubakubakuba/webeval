import { defineConfig } from 'vitepress'
import markdownItMathjax3 from 'markdown-it-mathjax3'
import markdownItFootnote from 'markdown-it-footnote'
import { withMermaid } from 'vitepress-plugin-mermaid'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "QtRVSim Web Evaluator Wiki",
  description: "A wiki page for WebEval",
	themeConfig: {
		nav: [
			{ text: 'Home', link: './' },
			{ text: 'WebEval', link: './wiki/WebEval' }
		],

		sidebar: [
			{
				text: 'WebEval',
				link: './wiki/WebEval/',
				items: [
					{
						text: 'User manual',
						link: './wiki/WebEval/user',
						collapsed: true,
						items: [
							{ text: 'Getting started', link: './wiki/WebEval/user/start' },
							{ text: 'Submitting a solution', link: './wiki/WebEval/user/submit' },
							{ text: 'Checking results', link: './wiki/WebEval/user/results' }
						]
					},
					{
						text: 'Developer manual',
						link: './wiki/WebEval/dev',
						collapsed: true,
						items: [
							{ text: 'Deploying the app', link: './wiki/WebEval/dev/deployment' },
							{ text: 'Creating a task', link: './wiki/WebEval/dev/tasks' },
							{ text: 'Admin panel', link: './wiki/WebEval/dev/admin-panel' },
							{ text: 'Evaluation', link: './wiki/WebEval/dev/evaluator' },
							{ text: 'Database schema', link: './wiki/WebEval/dev/database' }
						]
					}
				]
			},
		],

		socialLinks: [
			{ icon: 'github', link: 'https://gitlab.fel.cvut.cz/b35apo/qtrvsim-eval-web' }
		],

		editLink: {
			pattern: 'https://github.com/kubakubakuba/wiki/edit/main/:path'
		},

		search: {
			provider: 'local'
		},
	},

	markdown: {
		config: (md) => {
		  md.use(markdownItMathjax3);
		  md.use(markdownItFootnote)
		}
	},
})
