'use server';

import { createAppRouterRouteHandler } from '@flowglad/nextjs/server';
import { flowgladServer } from '@/flowglad';

const routeHandler = createAppRouterRouteHandler(flowgladServer);

export { routeHandler as GET, routeHandler as POST };
