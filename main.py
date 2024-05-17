import pygame

from numba import njit
from time import time
from math import log
from sys import exit

from config import *

# PYGAME SETUP
pygame.init()
if not MINIMISED: screen = pygame.display.set_mode(RESOLUTION)
elif MINIMISED: screen = pygame.display.set_mode((10, 10))
pygame.display.set_icon(pygame.image.load('images/mandelbrot-set.png'))
pygame.display.set_caption('Mandelbrot Set Renderer')
if MINIMISED: pygame.display.iconify()

class App:

	def __init__(self) -> None:
		self.fractal = Fractal(self)

	def format_time(self, secs: float | int) -> str: # -> hrs:mins:secs

		mins = secs // 60
		hours = mins // 60
		seconds = secs % 60
		mins %= 60

		formatted_time = '{:>02}:{:>02}:{:>02}.{:>03}'.format(int(hours), int(mins), int(seconds), str(seconds).split('.')[1][:3])
		return formatted_time

	def save(self, surface: pygame.Surface, location: str, name: str) -> None: # Save screen Surface to file

		print('\nSaving...')
		start_time = time()

		pygame.image.save(surface, f'{location}/{name}')

		finish_time = time()
		time_lapsed = self.format_time(finish_time - start_time)

		print(f"Saving Completed ({time_lapsed})")
		
class Fractal:

	def __init__(self, app: App) -> None:
		self.app = app

	def render(
		
		self,
		surface: pygame.Surface,
		gradient: pygame.Surface,
		mode: str,
		max_iter: int, 
		zoom: int | float,
		colour_density: int | float,
		offset: tuple | None = (0, 0),
		
	) -> pygame.PixelArray:

		print('\nRendering...')

		if mode == 'mandelbrot':

			screen_array = self.mandelbrot_set(
				
				screen_array = pygame.surfarray.array3d(surface),
				gradient_array = pygame.surfarray.array3d(gradient),
				gradient_size = gradient.get_width(),
				resolution = surface.get_size(),
				max_iter = max_iter,
				zoom = zoom,
				colour_density = colour_density,
				offset = offset
				
			)

		elif mode == 'julia':

			screen_array = self.julia_set(

				screen_array = pygame.surfarray.array3d(surface),
				gradient_array = pygame.surfarray.array3d(gradient),
				gradient_size = gradient.get_width(),
				resolution = surface.get_size(),
				max_iter = max_iter,
				colour_density = colour_density,
				zoom = zoom,
				julia_coordinates = offset
				
			)

		else: 
			
			print('\nUnrecognised Mode')
			pygame.quit()
			exit()

		return screen_array

	@ staticmethod
	@ njit(fastmath = True)
	def mandelbrot_set(

		screen_array: pygame.PixelArray,
		gradient_array: pygame.PixelArray,
		gradient_size: int | float,
		resolution: tuple,
		max_iter: int, 
		zoom: int | float, 
		colour_density: int | float,
		offset: tuple,
		
	) -> pygame.PixelArray:

		center_x, center_y = (resolution[0] / 2, resolution[1] / 2)

		for x in range(resolution[0]):
		
			for y in range(resolution[1]):
				
				c = (((x - center_x) / zoom) + offset[0]) + (((y - center_y) / zoom) - offset[1]) * 1j
				z = 0 + 0j
				
				for iter in range(max_iter):

					z = (z ** 2) + c
					
					if abs(z) > 3:
								
						smooth_iter = iter + 1 - log(log(abs(z))) / log(2)
						colour_val = int((smooth_iter * colour_density) % gradient_size)
								
						screen_array[x][y] = gradient_array[colour_val][0]

						break
						
					elif iter + 1 >= max_iter: screen_array[x][y] = (0, 0, 0)

		return screen_array
		
	@ staticmethod
	@ njit(fastmath = True)
	def julia_set(

		screen_array: pygame.PixelArray,
		gradient_array: pygame.PixelArray,
		gradient_size: int | float,
		resolution: tuple,
		max_iter: int, 
		zoom: int | float,
		colour_density: int | float,
		julia_coordinates: tuple
		
	) -> pygame.PixelArray:

		center_x, center_y = (resolution[0] / 2, resolution[1] / 2)

		for x in range(resolution[0]):
				
			for y in range(resolution[1]):

				c = julia_coordinates[0] + julia_coordinates[1] * 1j
				z = ((x - center_x) / zoom) + ((y - center_y) / zoom) * 1j
				
				for iter in range(max_iter):

					z = (z ** 2) + c
					
					if abs(z) > 3:

						smooth_iter = iter + 1 - log(log(abs(z))) / log(2)
						colour_val = int(((smooth_iter + 1) * colour_density) % gradient_size)
						screen_array[x][y] = gradient_array[colour_val][0]

						break
						
					elif iter + 1 >= max_iter: break
	
		return screen_array

def main() -> None:

	app = App()
	fractal = app.fractal

	image = pygame.Surface(RESOLUTION)

	start_time = time()
	screen_array = fractal.render(

		surface = image,
		gradient = pygame.image.load(GRADIENT).convert_alpha(),

		mode = MODE,
		max_iter = MAX_ITER,
		zoom = ZOOM,
		colour_density = COLOUR_DENSITY,
		offset = OFFSET,
		
	)
	finish_time = time()
	time_lapsed = app.format_time(finish_time - start_time)
	print(f"\nRendering Completed ({time_lapsed})")
			
	pygame.surfarray.blit_array(image, screen_array)

	file_name = f'{MODE.capitalize()} Set Render - MAX_ITER = {MAX_ITER}, ZOOM = {ZOOM}, OFFSET = {OFFSET}, COLOUR_DENSITY = {COLOUR_DENSITY}, SCALE = {SCALE}.png'

	if not MINIMISED:
		
		screen.blit(image, (0, 0))
		pygame.display.update()

	if AUTOSAVE: 
		
		if NOTIFICATIONS: toast(
			f'{MODE.capitalize()} Set Renderer', 
			f'Rendering Completed ({time_lapsed})',
		)
		app.save(image, 'renders', file_name)
	
	elif not AUTOSAVE:

		choice = input('\nSave? y/n > ')
		if choice.lower() == 'y': app.save(image, '/renders', file_name)

	print('\nRenderer Closed')
	pygame.quit()
	exit()
			
if __name__ == '__main__': main()