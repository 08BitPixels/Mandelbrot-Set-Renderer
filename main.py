import pygame
from multiprocessing import Process
from multiprocessing.shared_memory import ShareableList
from numba import njit
from numpy import ndarray, reshape
from win11toast import toast, notify, update_progress
from time import time
from math import log
from sys import exit
from constants import *

class App:

	def __init__(self) -> None:
		self.fractal = Fractal()

	def format_time(self, secs: float | int) -> str: # -> hrs:mins:secs

		mins = secs // 60
		hours = mins // 60
		seconds = secs % 60
		mins %= 60

		formatted_time = '{:>02}:{:>02}:{:>02}.{:>03}'.format(int(hours), int(mins), int(seconds), str(seconds).split('.')[1][:3])
		return formatted_time

	def save(self, surface: pygame.Surface, location: str, name: str) -> None: # Save screen Surface to file

		notify(
			progress = {
				'title': f'{MODE.capitalize()} Set Renderer',
				'status': 'Saving',
				'value': '0',
			}
		)

		print('\nSaving...')
		start_time = time()

		pygame.image.save(surface, f'{location}/{name}')

		finish_time = time()
		time_lapsed = self.format_time(finish_time - start_time)

		print(f"Saving Completed ({time_lapsed})")
		update_progress(
			progress = {
				'value': '100', 
				'status': f"Saving Completed ({time_lapsed})"
			}
		)
		
class Fractal:

	def __init__(self) -> None:
		pass

	def render(
		
		self,
		original_resolution: tuple,
		screen_arrays: ndarray,
		screen_coords: tuple,
		surface: str,
		surface_size: tuple,
		gradient: str,
		gradient_size: tuple,
		mode: str,
		max_iter: int, 
		zoom: int | float,
		colour_density: int | float,
		offset: tuple | None = (0, 0),
		
	) -> pygame.PixelArray:

		print('\nRendering...')
		gradient = pygame.image.fromstring(gradient, gradient_size, 'RGB')
		surface = pygame.image.fromstring(surface, surface_size, 'RGB')

		if mode == 'mandelbrot':

			screen_array = self.mandelbrot_set(
				
				screen_coords = screen_coords,
				screen_array = pygame.surfarray.array3d(surface),
				gradient_array = pygame.surfarray.array3d(gradient),
				gradient_size = gradient.get_width(),
				resolution = surface.get_size(),
				original_resolution = original_resolution,
				max_iter = max_iter,
				zoom = zoom,
				colour_density = colour_density,
				offset = offset
				
			)

		elif mode == 'julia':

			screen_array = self.julia_set(

				screen_coords = screen_coords,
				screen_array = pygame.surfarray.array3d(surface),
				gradient_array = pygame.surfarray.array3d(gradient),
				gradient_size = gradient.get_width(),
				resolution = surface.get_size(),
				original_resolution = original_resolution,
				max_iter = max_iter,
				colour_density = colour_density,
				zoom = zoom,
				julia_coordinates = offset
				
			)

		else: 
			
			print('\nUnrecognised Mode')
			pygame.quit()
			exit()

		screen_arrays[screen_coords[0] * COLS + screen_coords[1]] = screen_array

	@ staticmethod
	@ njit(fastmath = True)
	def mandelbrot_set(

		screen_coords: tuple,
		screen_array: pygame.PixelArray,
		gradient_array: pygame.PixelArray,
		gradient_size: int | float,
		resolution: tuple,
		original_resolution: tuple,
		max_iter: int, 
		zoom: int | float, 
		colour_density: int | float,
		offset: tuple,
		
	) -> pygame.PixelArray:

		center_x, center_y = (original_resolution[0] / 2) - (resolution[0] * screen_coords[0]), (original_resolution[1] / 2) - (resolution[1] * screen_coords[1])

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

		screen_coords: tuple,
		screen_array: pygame.PixelArray,
		gradient_array: pygame.PixelArray,
		gradient_size: int | float,
		resolution: tuple,
		original_resolution: tuple,
		max_iter: int, 
		zoom: int | float,
		colour_density: int | float,
		julia_coordinates: tuple
		
	) -> pygame.PixelArray:

		center_x, center_y = (original_resolution[0] / 2) - (resolution[0] * screen_coords[0]), (original_resolution[1] / 2) - (resolution[1] * screen_coords[1])

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

def main():

	app = App()
	fractal = app.fractal

	image = pygame.Surface(RESOLUTION)
	surfaces = ndarray((ROWS, COLS), pygame.Surface)
	processes = ndarray((ROWS, COLS), Process)
	screen_arrays = ShareableList([0 for i in range(CELLS)])

	for col in range(COLS):

		for row in range(ROWS):

			surfaces[row][col] = pygame.Surface((RESOLUTION[0] / COLS, RESOLUTION[1] / ROWS))

	for col in range(COLS):

		for row in range(ROWS):

			surface = surfaces[col][row]
			surface_string = pygame.image.tostring(surface, 'RGB')
			surface_size = surface.get_size()

			processes[row][col] = Process(

											target = fractal.render,
											args = (
														RESOLUTION,
														screen_arrays,
														(col, row),
														surface_string,
														surface_size,
														gradient_string,
														gradient_size,
														MODE,
														MAX_ITER,
														ZOOM,
														COLOUR_DENSITY,
														OFFSET

											)
									)

	start_time = time()

	for col in range(COLS):

		for row in range(ROWS):

			processes[row][col].start()

	finish_time = time()
	time_lapsed = app.format_time(finish_time - start_time)
	print(f"\nRendering Completed ({time_lapsed})")

	screen_arrays = reshape(screen_arrays, (COLS, ROWS))
	print(screen_arrays)

	for col in range(COLS): 

		for row in range(ROWS):
			
			pygame.surfarray.blit_array(surfaces[row][col], screen_arrays[row][col])
		
	for col in range(COLS): 

		for row in range(ROWS):
			
			image.blit(surfaces[row][col], ((RESOLUTION[0] / COLS) * col, (RESOLUTION[1] / ROWS) * row))

	file_name = f'{MODE.capitalize()} Set Render - MAX_ITER = {MAX_ITER}, ZOOM = {ZOOM}, OFFSET = {OFFSET}, COLOUR_DENSITY = {COLOUR_DENSITY}, SCALE = {SCALE}.png'

	if not MINIMISED:
		
		screen.blit(image, (0, 0))
		pygame.display.update()

	if AUTOSAVE: 
		
		toast(
			f'{MODE.capitalize()} Set Renderer', 
			f'Rendering Completed ({time_lapsed})',
		)
		app.save(image, 'renders', file_name)
	
	elif not AUTOSAVE:
	
		toast(
			f'{MODE.capitalize()} Set Renderer', 
			f'Rendering Completed ({time_lapsed})',
			button = 'Save',
			on_click = lambda args: app.save(image, 'renders', file_name)
		)

	print('\nRenderer Closed')
	pygame.quit()
	exit()
			
if __name__ == '__main__': 

	# PYGAME SETUP
	pygame.init()
	if not MINIMISED: screen = pygame.display.set_mode(RESOLUTION)
	elif MINIMISED: screen = pygame.display.set_mode((10, 10))
	pygame.display.set_icon(pygame.image.load('images/mandelbrot-set.png'))
	pygame.display.set_caption('Mandelbrot Set Renderer')
	if MINIMISED: pygame.display.iconify()
	
	gradient = pygame.image.load(GRADIENT)
	gradient_string = pygame.image.tostring(gradient, 'RGB')
	gradient_size = gradient.get_size()

	main()