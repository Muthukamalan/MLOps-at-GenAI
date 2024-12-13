export type SiteConfig = typeof siteConfig;

export const siteConfig: {
	name: string;
	description: string;
	navItems: {label: string; href: string}[]
	navMenuItems: {label: string; href: string}[]
	links: {
		[key: string]: string
	}
} = {
	name: "Stable Diffusion",
	description: "helper stable diffusion model",
	navItems: [
		{
			label: "blog",
			href: "https://muthukamalan.github.io/",
		},
	],
	navMenuItems: [
		// {
		// 	label: "Home",
		// 	href: "/",
		// },
	],
	links: {
		github: "https://github.com/Muthukamalan",
	},
};